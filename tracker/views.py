from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from .models import Profile, SecureMessage
from io import BytesIO
import hashlib
import base64
import os
from PIL import Image
from cryptography.fernet import Fernet


def home(request):
    return render(request, 'tracker/home.html')


def generate_key(password):
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)


def bytes_to_binary(data):
    return ''.join(format(byte, '08b') for byte in data)


def binary_to_bytes(binary):
    return bytes(int(binary[i:i + 8], 2) for i in range(0, len(binary), 8))


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


def signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Profile.objects.create(
            user=user,
            full_name=full_name
        )

        messages.success(request, 'Account created successfully. Please login.')
        return redirect('login')

    return render(request, 'tracker/signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'tracker/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    sent_count = SecureMessage.objects.filter(sender=request.user).count()
    inbox_count = SecureMessage.objects.filter(receiver=request.user).count()
    unread_count = SecureMessage.objects.filter(receiver=request.user, is_read=False).count()

    return render(request, 'tracker/dashboard.html', {
        'sent_count': sent_count,
        'inbox_count': inbox_count,
        'unread_count': unread_count,
    })


@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.username}
    )

    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name')
        profile.phone = request.POST.get('phone')
        profile.location = request.POST.get('location')
        profile.bio = request.POST.get('bio')

        if request.FILES.get('avatar'):
            profile.avatar = request.FILES.get('avatar')

        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'tracker/profile.html', {'profile': profile})


@login_required
def send_message(request):
    users = User.objects.exclude(id=request.user.id)

    if request.method == 'POST':
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject')
        note = request.POST.get('note')
        password = request.POST.get('password')

        image_file = request.FILES.get('image')
        audio_file = request.FILES.get('audio')

        receiver = get_object_or_404(User, id=receiver_id)

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
            messages.error(request, 'Audio file is too large for this image.')
            return redirect('send_message')

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

        buffer = BytesIO()
        image.save(buffer, format='PNG')

        hidden_file_name = f'hidden_{request.user.username}_{receiver.username}.png'

        secure_message = SecureMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=subject,
            note=note,
            original_image=image_path,
            original_audio=audio_path,
        )

        secure_message.hidden_image.save(
            hidden_file_name,
            ContentFile(buffer.getvalue()),
            save=True
        )

        messages.success(request, 'Secure message sent successfully.')
        return redirect('outbox')

    return render(request, 'tracker/send_message.html', {'users': users})


@login_required
def inbox(request):
    messages_list = SecureMessage.objects.filter(receiver=request.user).order_by('-created_at')
    return render(request, 'tracker/inbox.html', {'messages_list': messages_list})


@login_required
def outbox(request):
    messages_list = SecureMessage.objects.filter(sender=request.user).order_by('-created_at')
    return render(request, 'tracker/outbox.html', {'messages_list': messages_list})


@login_required
def message_detail(request, message_id):
    secure_message = get_object_or_404(SecureMessage, id=message_id)

    if secure_message.receiver != request.user and secure_message.sender != request.user:
        return redirect('dashboard')

    unlocked = False
    extracted_audio_url = None

    if secure_message.receiver == request.user:
        secure_message.is_read = True
        secure_message.save()

    if request.method == 'POST':
        password = request.POST.get('password')

        try:
            image = Image.open(secure_message.hidden_image.path).convert('RGB')
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

            key = generate_key(password)
            cipher = Fernet(key)
            audio_data = cipher.decrypt(encrypted_audio)

            output_audio_name = f'extracted_message_{secure_message.id}.wav'
            output_audio_path = os.path.join('media', output_audio_name)

            with open(output_audio_path, 'wb') as file:
                file.write(audio_data)

            extracted_audio_url = '/media/' + output_audio_name
            unlocked = True
            messages.success(request, 'Audio unlocked successfully.')

        except Exception:
            messages.error(request, 'Wrong password or audio could not be extracted.')

    return render(request, 'tracker/message_detail.html', {
        'secure_message': secure_message,
        'unlocked': unlocked,
        'extracted_audio_url': extracted_audio_url
    })