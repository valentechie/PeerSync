const PHOTO_SIZE = 256;
const JPEG_QUALITY = 0.85;
const MAX_ORIGINAL_BYTES = 25 * 1024 * 1024;

export class PhotoError extends Error {}

/**
 * Recorta la imagen en un cuadrado centrado y la reduce antes de subirla.
 * Al redibujarla se pierden sus datos ocultos, como la ubicación GPS de una foto de móvil.
 */
export async function preparePhoto(file: File): Promise<File> {
  if (file.size > MAX_ORIGINAL_BYTES) throw new PhotoError('The image is too large. Try one under 25 MB.');

  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new PhotoError("Couldn't read that image. Try a JPEG, PNG or WebP.");
  }
  const side = Math.min(bitmap.width, bitmap.height);
  const canvas = document.createElement('canvas');
  canvas.width = PHOTO_SIZE;
  canvas.height = PHOTO_SIZE;
  const context = canvas.getContext('2d');
  if (!context) throw new PhotoError("Your browser couldn't process the image.");
  // Sin esto, las zonas transparentes de un PNG quedarían negras en el JPEG.
  context.fillStyle = '#ffffff';
  context.fillRect(0, 0, PHOTO_SIZE, PHOTO_SIZE);
  context.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, PHOTO_SIZE, PHOTO_SIZE);
  bitmap.close();

  const blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY));
  if (!blob) throw new PhotoError("Your browser couldn't process the image.");
  return new File([blob], 'photo.jpg', { type: 'image/jpeg' });
}
