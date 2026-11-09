import { useEffect, useId, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '../../components/ui/button.tsx';
import { Input } from '../../components/ui/input.tsx';
import { Label } from '../../components/ui/label.tsx';
import { DiaryError, errorMessage } from '../../lib/httpError.ts';
import { useRequestScope } from '../../useRequestScope.ts';
import { OCR_FALLBACK, readingsApi } from './api.ts';
import type { PhotoAction, Reading, ReadingInput } from './api.ts';
import { EMPTY_CROP, editPhotoAction, photoProblem, resolveCrop, stripDataUrl } from './photo.ts';
import type { CropFields } from './photo.ts';
import { MAX_READING_DIGITS } from './value.ts';
import { lowerReadingWarning } from './warning.ts';

const schema = z.object({
  recorded_at: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$/, 'Ingresá una fecha ISO con segundos y zona horaria.'),
  value_kwh: z.string().min(1, 'Ingresá la lectura.').max(MAX_READING_DIGITS).regex(/^[0-9]+$/, 'Ingresá solo dígitos enteros.'),
  confirmed: z.boolean().refine(value => value, 'Confirmá la lectura antes de guardar.'),
});

interface SelectedPhoto { base64: string; url: string }

function readBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('No se pudo leer la fotografía.'));
    reader.onload = () => {
      const value = typeof reader.result === 'string' ? stripDataUrl(reader.result) : null;
      if (value === null) reject(new Error('No se pudo leer la fotografía.'));
      else resolve(value);
    };
    reader.readAsDataURL(file);
  });
}

export function ReadingForm({ reading, rows, meterId, busy, save, cancel }: {
  reading: Reading | null; rows: Reading[]; meterId: string; busy: boolean;
  save: (input: ReadingInput, photoAction: PhotoAction) => Promise<'done' | 'review'>; cancel: () => void;
}) {
  const id = useId();
  const scope = useRequestScope();
  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm<z.input<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { recorded_at: reading?.recorded_at ?? '', value_kwh: reading?.value_kwh ?? '', confirmed: false },
  });
  const warning = lowerReadingWarning(rows, meterId, watch('recorded_at'), watch('value_kwh'), reading?.id);
  const [photo, setPhoto] = useState<SelectedPhoto | null>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [cropFields, setCropFields] = useState<CropFields>(EMPTY_CROP);
  const [removePhoto, setRemovePhoto] = useState(false);
  const [photoError, setPhotoError] = useState('');
  const [ocrMessage, setOcrMessage] = useState('');
  const [ocrError, setOcrError] = useState('');
  const [ocrLoading, setOcrLoading] = useState(false);
  const pending = busy || isSubmitting || ocrLoading;

  // The preview URL is held only while the unconfirmed photo stays in memory.
  useEffect(() => {
    const url = photo?.url;
    if (!url) return;
    return () => URL.revokeObjectURL(url);
  }, [photo?.url]);

  function clearPhoto() {
    setPhoto(null); setSize({ width: 0, height: 0 }); setCropFields(EMPTY_CROP);
    setOcrMessage(''); setOcrError(''); setRemovePhoto(false);
  }

  async function choosePhoto(file: File | undefined) {
    setPhotoError(''); setOcrMessage(''); setOcrError('');
    if (!file) return;
    const problem = photoProblem(file);
    if (problem) { setPhotoError(problem); return; }
    let base64: string;
    try { base64 = await readBase64(file); }
    catch { setPhotoError('No se pudo leer la fotografía.'); return; }
    setPhoto({ base64, url: URL.createObjectURL(file) });
    setSize({ width: 0, height: 0 });
    setCropFields(EMPTY_CROP);
    setRemovePhoto(false);
  }

  async function requestOcr() {
    if (!photo) return;
    if (size.width === 0 || size.height === 0) {
      setOcrError('Esperá a que la vista previa termine de cargar.');
      return;
    }
    const crop = resolveCrop(cropFields, size.width, size.height);
    if (crop === null) {
      setOcrError('El recorte debe ser un rectángulo dentro de la fotografía.');
      return;
    }
    setOcrError(''); setOcrMessage('');
    const request = scope.begin('ocr');
    setOcrLoading(true);
    try {
      const result = await readingsApi.ocr(meterId, photo.base64, crop, request.signal);
      if (!request.isCurrent()) return;
      if (result.status === 'suggested') {
        // A suggestion is never saved: it only fills the editable, unconfirmed field.
        setValue('value_kwh', result.value_kwh);
        setValue('confirmed', false);
        setOcrMessage('Valor sugerido por OCR. Revisalo y confirmá antes de guardar.');
      } else setOcrMessage(result.message);
    } catch (reason: unknown) {
      if (!request.isCurrent()) return;
      if (reason instanceof DiaryError && (reason.status === 401 || reason.status === 403)) setOcrError(errorMessage(reason));
      else setOcrMessage(OCR_FALLBACK);
    } finally {
      if (request.isCurrent()) setOcrLoading(false);
    }
  }

  return <form noValidate aria-label={reading ? 'Corregir lectura' : 'Registrar lectura'} className="space-y-3" onSubmit={handleSubmit(async values => {
    const action: PhotoAction = reading ? editPhotoAction(photo !== null, removePhoto) : 'keep';
    const result = await save({
      recorded_at: values.recorded_at, value_kwh: values.value_kwh, confirmed: true, photo_base64: photo?.base64 ?? null,
    }, action);
    if (result === 'review') setValue('confirmed', false);
  })}>
    <Label htmlFor={`${id}-date`}>Fecha y hora con zona horaria</Label>
    <Input id={`${id}-date`} {...register('recorded_at')} placeholder="2026-11-07T12:00:00-03:00" disabled={pending} aria-invalid={Boolean(errors.recorded_at)} aria-describedby={`${id}-date-help${errors.recorded_at ? ` ${id}-date-error` : ''}`} />
    <p id={`${id}-date-help`}>Usá formato ISO con segundos y zona, por ejemplo 2026-11-07T12:00:00-03:00. El historial se muestra en hora de Buenos Aires.</p>
    {errors.recorded_at && <p id={`${id}-date-error`} role="alert">{errors.recorded_at.message}</p>}
    <Label htmlFor={`${id}-value`}>Lectura acumulada en kWh</Label>
    <Input id={`${id}-value`} inputMode="numeric" maxLength={MAX_READING_DIGITS} {...register('value_kwh')} disabled={pending} aria-invalid={Boolean(errors.value_kwh)} aria-describedby={errors.value_kwh ? `${id}-value-error` : undefined} />
    {errors.value_kwh && <p id={`${id}-value-error`} role="alert">{errors.value_kwh.message}</p>}
    {warning && <p role="status">La lectura es menor que la lectura anterior. Revisala; podés confirmarla igualmente.</p>}
    <div className="space-y-2">
      <Label htmlFor={`${id}-photo`}>Fotografía (JPG, PNG o WebP, hasta 5 MB)</Label>
      <Input id={`${id}-photo`} type="file" accept="image/jpeg,image/png,image/webp" disabled={pending}
        aria-describedby={`${id}-photo-help`} onChange={event => {
          const file = event.target.files?.[0];
          event.target.value = '';
          void choosePhoto(file);
        }} />
      <p id={`${id}-photo-help`}>Opcional y privada. Para OCR, recortá solo los dígitos enteros del registro de kWh.</p>
      {photoError && <p role="alert">{photoError}</p>}
      {photo && <div className="space-y-2">
        <img src={photo.url} alt="Vista previa de la fotografía" className="max-w-full" onLoad={event => {
          setSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight });
        }} />
        <Button type="button" variant="outline" disabled={pending} onClick={clearPhoto}>Quitar foto seleccionada</Button>
        {size.width > 0 && size.height > 0 && <div className="space-y-2">
          <p>Recorte para OCR en píxeles de la foto original ({size.width}×{size.height}). Un campo vacío usa el borde de la foto.</p>
          <div className="grid grid-cols-2 gap-2">
            <div><Label htmlFor={`${id}-crop-x`}>Recorte X</Label><Input id={`${id}-crop-x`} inputMode="numeric" value={cropFields.x} disabled={pending} onChange={event => setCropFields({ ...cropFields, x: event.target.value })} /></div>
            <div><Label htmlFor={`${id}-crop-y`}>Recorte Y</Label><Input id={`${id}-crop-y`} inputMode="numeric" value={cropFields.y} disabled={pending} onChange={event => setCropFields({ ...cropFields, y: event.target.value })} /></div>
            <div><Label htmlFor={`${id}-crop-width`}>Recorte ancho</Label><Input id={`${id}-crop-width`} inputMode="numeric" value={cropFields.width} disabled={pending} onChange={event => setCropFields({ ...cropFields, width: event.target.value })} /></div>
            <div><Label htmlFor={`${id}-crop-height`}>Recorte alto</Label><Input id={`${id}-crop-height`} inputMode="numeric" value={cropFields.height} disabled={pending} onChange={event => setCropFields({ ...cropFields, height: event.target.value })} /></div>
          </div>
          <Button type="button" variant="outline" disabled={pending} onClick={() => void requestOcr()}>{ocrLoading ? 'Consultando OCR…' : 'Leer dígitos con OCR'}</Button>
        </div>}
        {ocrMessage && <p role="status">{ocrMessage}</p>}
        {ocrError && <p role="alert">{ocrError}</p>}
      </div>}
      {reading && <div className="space-y-2">
        <p>{reading.has_photo ? 'Esta lectura tiene una fotografía adjunta.' : 'Esta lectura no tiene fotografía.'}{photo ? ' La foto seleccionada la reemplazará al guardar.' : ''}</p>
        {reading.has_photo && !photo && <Button type="button" variant="outline" disabled={pending} onClick={() => setRemovePhoto(current => !current)}>{removePhoto ? 'Mantener la foto actual' : 'Quitar foto al guardar'}</Button>}
        {removePhoto && <p role="status">La fotografía actual se quitará al guardar.</p>}
      </div>}
    </div>
    <div><input id={`${id}-confirm`} type="checkbox" {...register('confirmed')} disabled={pending} aria-invalid={Boolean(errors.confirmed)} aria-describedby={errors.confirmed ? `${id}-confirm-error` : undefined} />{' '}<Label htmlFor={`${id}-confirm`}>Confirmo que revisé la lectura</Label></div>
    {errors.confirmed && <p id={`${id}-confirm-error`} role="alert">{errors.confirmed.message}</p>}
    <div className="flex flex-wrap gap-2"><Button disabled={pending}>{reading ? 'Guardar corrección' : 'Guardar lectura'}</Button>
      {reading && <Button type="button" variant="outline" disabled={pending} onClick={cancel}>Cancelar corrección de lectura</Button>}</div>
  </form>;
}
