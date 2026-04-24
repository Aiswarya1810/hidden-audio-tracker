from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from PIL import Image
from cryptography.fernet import Fernet
import os
import base64
import hashlib


def home(request):
    return render(request, 'tracker/home.html')


# generate encryption key from password
def generate_key(password):
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)


def bytes_to_binary(data):
    return ''.join(format(byte, '08b') for byte in data)


def binary_to_bytes(binary):
    return bytes(int(binary[i:i+8], 2) for i in range(0, len(binary), 8))


# ------------------ IMPOSE ------------------
def impose_audio(request):
    message = None
    output_file_url = None

    if request.method == 'POST':
        image_file = request.FILES['image']
        audio_file = request.FILES['audio']
        password = request.POST['password']

        fs = FileSystemStorage()

        image_path = fs.save(image_file.name, image_file)
        audio_path = fs.save(audio_file.name, audio_file)

        image_full_path = fs.path(image_path)
        audio_full_path = fs.path(audio_path)

        with open(audio_full_path, 'rb') as file:
            audio_data = file.read()

        key = generate_key(password)
        cipher = Fernet(key)
        encrypted_audio = cipher.encrypt(audio_data)

        audio_length = len(encrypted_audio)
        final_data = audio_length.to_bytes(4, 'big') + encrypted_audio
        binary_data = bytes_to_binary(final_data)

        image = Image.open(image_full_path).convert('RGB')
        pixels = list(image.getdata())

        max_capacity = len(pixels) * 3

        if len(binary_data) > max_capacity:
            message = "❌ Audio too large for this image"
            return render(request, 'tracker/impose.html', {'message': message})

        new_pixels = []
        data_index = 0

        for pixel in pixels:
            r, g, b = pixel

            if data_index < len(binary_data):
                r = (r & ~1) | int(binary_data[data_index])
                data_index += 1

            if data_index < len(binary_data):
                g = (g & ~1) | int(binary_data[data_index])
                data_index += 1

            if data_index < len(binary_data):
                b = (b & ~1) | int(binary_data[data_index])
                data_index += 1

            new_pixels.append((r, g, b))

        image.putdata(new_pixels)

        output_name = 'hidden_audio.png'
        output_path = os.path.join('media', output_name)
        image.save(output_path)

        output_file_url = '/media/' + output_name
        message = "✅ Audio hidden successfully!"

    return render(request, 'tracker/impose.html', {
        'message': message,
        'output_file_url': output_file_url
    })


# ------------------ EXTRACT ------------------
def extract_audio(request):
    message = None
    audio_url = None

    if request.method == 'POST':
        image_file = request.FILES['image']
        password = request.POST['password']

        fs = FileSystemStorage()
        image_path = fs.save(image_file.name, image_file)
        image_full_path = fs.path(image_path)

        image = Image.open(image_full_path).convert('RGB')
        pixels = list(image.getdata())

        binary_data = ""

        for pixel in pixels:
            r, g, b = pixel
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)

        length_binary = binary_data[:32]
        audio_length = int(length_binary, 2)

        encrypted_binary = binary_data[32:32 + audio_length * 8]
        encrypted_audio = binary_to_bytes(encrypted_binary)

        try:
            key = generate_key(password)
            cipher = Fernet(key)
            audio_data = cipher.decrypt(encrypted_audio)

            output_audio_name = 'extracted.wav'
            output_audio_path = os.path.join('media', output_audio_name)

            with open(output_audio_path, 'wb') as file:
                file.write(audio_data)

            audio_url = '/media/' + output_audio_name
            message = "✅ Audio extracted successfully!"

        except Exception:
            message = "❌ Wrong password or invalid image"

    return render(request, 'tracker/extract.html', {
        'message': message,
        'audio_url': audio_url
    })