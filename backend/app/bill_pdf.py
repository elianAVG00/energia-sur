"""Bounded local PDF inspection for CU06; it is not malware detection."""

import io
import multiprocessing
import resource
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess

MAX_FILE_BYTES = 5_000_000
MAX_PDF_NODES = 100_000
MAX_PDF_PAGES = 1_000
PDF_MEMORY_BYTES = 512 * 1024 * 1024
PDF_CPU_SECONDS = 10
PDF_TIMEOUT_SECONDS = 10.0
_FORBIDDEN_KEYS = frozenset({
    "/AA", "/A", "/OpenAction", "/JS", "/JavaScript", "/Launch",
    "/EmbeddedFiles", "/EmbeddedFile", "/EF", "/XFA", "/RichMedia",
    "/SubmitForm", "/ImportData", "/GoToR", "/URI", "/AcroForm",
})


class InvalidBillPdf(ValueError):
    """A PDF failed validation or could not be safely inspected."""


def _inspect(data: bytes) -> None:
    """Inspect reachable object dictionaries; run only in a bounded worker."""
    from pypdf import PdfReader
    from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject

    if not data.startswith(b"%PDF-") or len(data) > MAX_FILE_BYTES:
        raise InvalidBillPdf("Invalid PDF.")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted:
        raise InvalidBillPdf("Encrypted PDF.")
    page_count = len(reader.pages)
    if not 1 <= page_count <= MAX_PDF_PAGES:
        raise InvalidBillPdf("Invalid page count.")
    for page in reader.pages:
        if page.get("/Type") != "/Page" or len(page.mediabox) != 4:
            raise InvalidBillPdf("Invalid page.")

    pending = [reader.trailer]
    seen_references: set[tuple[int, int]] = set()
    seen_containers: set[int] = set()
    count = 0
    while pending:
        node = pending.pop()
        count += 1
        if count > MAX_PDF_NODES:
            raise InvalidBillPdf("PDF object limit exceeded.")
        if isinstance(node, IndirectObject):
            ref = (node.idnum, node.generation)
            if ref in seen_references:
                continue
            seen_references.add(ref)
            resolved = node.get_object()
            if resolved is None:
                raise InvalidBillPdf("Invalid PDF reference.")
            pending.append(resolved)
        elif isinstance(node, (DictionaryObject, ArrayObject)):
            if id(node) in seen_containers:
                continue
            seen_containers.add(id(node))
            if isinstance(node, DictionaryObject):
                for key in node:
                    if str(key) in _FORBIDDEN_KEYS:
                        raise InvalidBillPdf("Unsupported active PDF content.")
                    pending.append(node.raw_get(key))
            else:
                pending.extend(node)
        elif isinstance(node, NameObject) and str(node) in _FORBIDDEN_KEYS:
            raise InvalidBillPdf("Unsupported active PDF content.")


def _worker(connection: Connection, data: bytes) -> None:
    try:
        resource.setrlimit(resource.RLIMIT_AS, (PDF_MEMORY_BYTES, PDF_MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_CPU, (PDF_CPU_SECONDS, PDF_CPU_SECONDS))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        _inspect(data)
        connection.send(True)
    except BaseException:
        try:
            connection.send(False)
        except (OSError, EOFError):
            pass
    finally:
        connection.close()


def _stop(process: BaseProcess) -> None:
    process.join(timeout=1)
    if process.is_alive():
        process.terminate()
        process.join(timeout=2)
    if process.is_alive():
        process.kill()
        process.join(timeout=1)
    if process.is_alive():
        raise InvalidBillPdf("PDF worker could not be stopped.")


def validate_bill_pdf(data: bytes) -> None:
    """Fail closed on invalid input, timeout or worker failure."""
    if not data or len(data) > MAX_FILE_BYTES:
        raise InvalidBillPdf("Invalid PDF size.")
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(child, data), daemon=True)
    process.start()
    child.close()
    try:
        if not parent.poll(PDF_TIMEOUT_SECONDS):
            raise InvalidBillPdf("PDF worker timeout.")
        try:
            valid = parent.recv()
        except (EOFError, OSError):
            raise InvalidBillPdf("PDF worker failed.") from None
        if valid is not True:
            raise InvalidBillPdf("Invalid PDF.")
    finally:
        parent.close()
        _stop(process)
