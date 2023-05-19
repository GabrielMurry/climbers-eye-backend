from PIL import Image, ImageEnhance
from io import BytesIO
import base64

def base64_string_to_image(drawing, photo):
    drawing_image = Image.open(BytesIO(base64.b64decode(drawing)))
    photo_image = Image.open(BytesIO(base64.b64decode(photo)))
    return drawing_image, photo_image

def increase_drawing_opacity(drawing_image):
    # increase opacity of drawings, but NOT the transparent background
    # Split the image into channels 
    r, g, b, a = drawing_image.split()
    # Increase the opacity of the alpha channel
    # Multiplication - transparent alpha is 0 so it will stay 0
    # Multiply by 2.5 since we want to increase it by 2.5 to get 255. Our original opacity is 0.4, multiply that by 2.5 and we get 1
    a = a.point(lambda x: x * 2)
    # Merge the channels back into an RGBA image
    return Image.merge('RGBA', (r, g, b, a))

def mask_drawing(drawing_image, photo_image):
    # Create a blank white mask, same size, and gray-scaled (mode 'L')
    mask = Image.new("L", drawing_image.size, 'WHITE')
    # Paste our drawing over new blank mask, masking the drawings with the drawings themselves
    mask.paste(drawing_image, mask=drawing_image)
    # Cut out the photo where we drew using our drawing mask
    drawing_image = Image.composite(drawing_image, photo_image, mask)
    return drawing_image

def combine_images(drawing_image, photo_image):
    # gray-scale photo image, but before converting to 'L' mode, grab the alpha channel
    # converting to 'L' mode (Luminance) gray-scales image efficiently through a single 8-bit channel per pixel, rather than RGBA which provides 4 x 8-bit channels per pixel
    alpha_channel  = photo_image.getchannel('A')
    gray_channels = photo_image.convert('L')
    # convert back to RGBA but merge the gray channel values as 'RGB' and the original alpha channel for 'A', all as a tuple.
    photo_image_result = Image.merge('RGBA', (gray_channels, gray_channels, gray_channels, alpha_channel))
    # darken photo image background before alpha compositing the images together
    brightnessLevel = ImageEnhance.Brightness(photo_image_result)
    # factor > 1 brightens. factor < 1 darkens
    factor = 0.4
    photo_image_result = brightnessLevel.enhance(factor)
    # alpha composite to place drawing image on top of manipulated photo image
    photo_image_result.alpha_composite(drawing_image)
    return photo_image_result

def image_to_base64_string(result):
    buffered = BytesIO()
    result.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")