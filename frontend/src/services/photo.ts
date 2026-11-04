const PHOTO_SIZE = 256;
const JPEG_QUALITY = 0.85;
const MAX_ORIGINAL_BYTES = 25 * 1024 * 1024;

export class PhotoError extends Error {}

/**
 * Recorta la imagen en un cuadrado centrado y la reduce antes de subirla.
 * Al redibujarla se pierden sus datos ocultos, como la ubicación GPS de una foto de móvil.
 */
export async function preparePhoto(file: File): Promise<File> {
  if (file.size > MAX_ORIGINAL_BYTES) throw new PhotoError('La imagen es demasiado grande. Prueba con otra de menos de 25 MB.');

  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new PhotoError('No se pudo leer esa imagen. Prueba con un JPEG, PNG o WebP.');
  }
  const side = Math.min(bitmap.width, bitmap.height);
  const canvas = document.createElement('canvas');
  canvas.width = PHOTO_SIZE;
  canvas.height = PHOTO_SIZE;
  const context = canvas.getContext('2d');
  if (!context) throw new PhotoError('Tu navegador no pudo procesar la imagen.');
  // Sin esto, las zonas transparentes de un PNG quedarían negras en el JPEG.
  context.fillStyle = '#ffffff';
  context.fillRect(0, 0, PHOTO_SIZE, PHOTO_SIZE);
  context.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, PHOTO_SIZE, PHOTO_SIZE);
  bitmap.close();

  const blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY));
  if (!blob) throw new PhotoError('Tu navegador no pudo procesar la imagen.');
  return new File([blob], 'foto.jpg', { type: 'image/jpeg' });
}
