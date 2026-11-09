/** CU05 photo and manual-crop rules; the backend remains authoritative. */
import type { Crop, PhotoAction } from './api.ts';

export const MAX_PHOTO_BYTES = 5_000_000;
const PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const BASE64_PHOTO = /^data:image\/(?:jpeg|png|webp);base64,([A-Za-z0-9+/]+={0,2})$/;

export interface CropFields { x: string; y: string; width: string; height: string }
export const EMPTY_CROP: CropFields = { x: '', y: '', width: '', height: '' };

/** Reject unsupported files before reading them; the server validates the bytes. */
export function photoProblem(file: { type: string; size: number }): string | null {
  if (file.size === 0) return 'La fotografía está vacía.';
  if (!PHOTO_TYPES.some(type => type === file.type)) return 'Elegí una fotografía JPG, PNG o WebP.';
  if (file.size > MAX_PHOTO_BYTES) return 'La fotografía supera los 5 MB.';
  return null;
}

/** Data URLs from FileReader carry a media-type prefix the API does not accept. */
export function stripDataUrl(value: string): string | null {
  return BASE64_PHOTO.exec(value)?.[1] ?? null;
}

/** Replace wins over removal: the form never requests both actions. */
export function editPhotoAction(hasNewPhoto: boolean, removeRequested: boolean): PhotoAction {
  if (hasNewPhoto) return 'replace';
  return removeRequested ? 'remove' : 'keep';
}

function pixel(value: string, fallback: number): number | null {
  const text = value.trim();
  if (text === '') return fallback;
  if (!/^[0-9]{1,9}$/.test(text)) return null;
  const number = Number(text);
  return Number.isSafeInteger(number) ? number : null;
}

/** Empty fields extend to the image edge; every coordinate is an original-image pixel. */
export function resolveCrop(fields: CropFields, imageWidth: number, imageHeight: number): Crop | null {
  if (!Number.isSafeInteger(imageWidth) || !Number.isSafeInteger(imageHeight) ||
      imageWidth <= 0 || imageHeight <= 0) return null;
  const x = pixel(fields.x, 0);
  const y = pixel(fields.y, 0);
  if (x === null || y === null) return null;
  const width = pixel(fields.width, imageWidth - x);
  const height = pixel(fields.height, imageHeight - y);
  if (width === null || height === null || width <= 0 || height <= 0) return null;
  if (x + width > imageWidth || y + height > imageHeight) return null;
  return { x, y, width, height };
}
