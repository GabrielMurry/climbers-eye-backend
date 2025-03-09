from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile
from PIL import Image

class TestImage:
    @staticmethod
    def display_image(uploaded_file: UploadedFile) -> None:
        """
        Display the uploaded image using PIL.
        """
        if not uploaded_file:
            print('No file provided.')
            return
        try:
            # Check if the uploaded file is a file-like object
            if isinstance(uploaded_file, InMemoryUploadedFile):
                # Open the image using PIL
                image = Image.open(uploaded_file)
                # Display the image
                image.show()
            else:
                print('Unsupported file type. Expected a file-like object.')
        except Exception as e:
            print(f'An error occurred while displaying the image: {str(e)}')