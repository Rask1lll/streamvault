import os
import io
import qrcode
import uuid
from django.conf import settings
from .models import Folder, File, FileUploadSession
from .serializers import FolderSerializer, FileSerializer
from django.templatetags.static import static
import mimetypes
from django.http import FileResponse, Http404
from django.http import JsonResponse
from django.utils import timezone
from .permissions import IsAdminOrSuperUserRole
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.contrib.auth import get_user_model


User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {"user": UserSerializer(user).data, "tokens": tokens},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = get_tokens_for_user(user)
            return Response(
                {"user": UserSerializer(user).data, "tokens": tokens},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        return self._update_user(request, partial=False)

    def patch(self, request):
        return self._update_user(request, partial=True)

    def _update_user(self, request, partial=False):
        user = request.user
        data = request.data.copy()

        # Проверяем, если пользователь пытается поменять role
        if "role" in data:
            # Разрешаем, если суперюзер или роль = SuperUser/Admin
            if not getattr(user, "is_superuser", False) and not (
                    user.role and user.role.role_name in ["SuperUser", "Admin"]
            ):
                return Response(
                    {"detail": "У вас недостаточно прав для изменения роли."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = UserSerializer(user, data=data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Данные обновлены", "user": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==============================
# 🔹 Папки
# ==============================
class FolderCreateAPIView(APIView):
    permission_classes = [IsAdminOrSuperUserRole]

    """Создание новой папки"""

    def get(self, request):
        folders = Folder.objects.all().order_by('-created_at')
        serializer = FolderSerializer(folders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FolderSerializer(data=request.data)
        if serializer.is_valid():
            folder = serializer.save()
            return Response(FolderSerializer(folder).data, status=201)
        return Response(serializer.errors, status=400)


class FolderViewByTokenAPIView(APIView):
    """Просмотр содержимого папки по токену"""
    def get(self, request, token):
        try:
            folder = Folder.objects.get(token=token)
        except Folder.DoesNotExist:
            return Response({'error': 'Folder not found'}, status=404)

        subfolders = Folder.objects.filter(parent=folder)
        files = File.objects.filter(folder=folder)

        return Response({
            'folder': FolderSerializer(folder).data,
            'subfolders': FolderSerializer(subfolders, many=True).data,
            'files': FileSerializer(files, many=True).data
        })


class FolderUpdateAPIView(APIView):
    permission_classes = [IsAdminOrSuperUserRole]

    """Переименование или перемещение папки по токену"""
    def patch(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            folder = Folder.objects.get(token=token)
        except Folder.DoesNotExist:
            return Response({"error": "Folder not found"}, status=404)

        name = request.data.get("name")
        parent_id = request.data.get("parent")

        # Переименование
        if name:
            folder.name = name

        # Перемещение
        if parent_id is not None:
            if parent_id == "":
                folder.parent = None
            else:
                try:
                    folder.parent = Folder.objects.get(pk=parent_id)
                except Folder.DoesNotExist:
                    return Response({"error": "Parent folder not found"}, status=404)

        folder.save()
        return Response(FolderSerializer(folder).data, status=200)


# ==============================
# 🔹 QR-коды
# ==============================
class QRCodeAPIView(APIView):
    """
    Генерация QR-кода по токену (файла или папки)
    """
    def get(self, request, token):
        try:
            obj = File.objects.get(token=token)
            url = request.build_absolute_uri(f'/storage/api/v3/view/{token}/')
        except File.DoesNotExist:
            try:
                obj = Folder.objects.get(token=token)
                url = request.build_absolute_uri(f'/storage/api/v3/folder/{token}/')
            except Folder.DoesNotExist:
                return Response({'error': 'Object not found'}, status=404)

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return FileResponse(buffer, content_type="image/png")


# ==============================
# 🔹 Chunk Upload
# ==============================
# views.py
class ChunkInitAPIView(APIView):
    permission_classes = [IsAdminOrSuperUserRole]

    """
    1️⃣ Инициализация загрузки по чанкам
    """

    def post(self, request):
        folder_id = request.data.get("folder_id")
        total_chunks = request.data.get("total_chunks")
        file_name = request.data.get("file_name")

        if not total_chunks or not file_name:
            return Response(
                {"error": "total_chunks и file_name обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        folder = None
        if folder_id:
            folder = Folder.objects.filter(id=folder_id).first()
            if not folder:
                return Response({"error": "Папка не найдена"}, status=404)

        upload_id = str(uuid.uuid4())
        session = FileUploadSession.objects.create(
            folder=folder,
            upload_id=upload_id,
            total_chunks=int(total_chunks),
            file_name=file_name,
        )
        return Response(
            {"upload_id": upload_id, "total_chunks": total_chunks, "file_name": file_name},
            status=201,
        )


class ChunkUploadAPIView(APIView):
    """
    2️⃣ Приём чанков
    Headers:
      X-Upload-ID, X-Chunk-Index
    Body: бинарные данные
    """
    permission_classes = [IsAdminOrSuperUserRole]

    def post(self, request):
        upload_id = request.headers.get("X-Upload-ID")
        chunk_index = request.headers.get("X-Chunk-Index")

        if not upload_id or chunk_index is None:
            return Response(
                {"error": "X-Upload-ID и X-Chunk-Index обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = FileUploadSession.objects.filter(upload_id=upload_id, is_complete=False).first()
        if not session:
            return Response({"error": "Сессия не найдена или завершена"}, status=404)

        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads", upload_id)
        os.makedirs(temp_dir, exist_ok=True)

        chunk_path = os.path.join(temp_dir, f"chunk_{chunk_index}")
        with open(chunk_path, "wb") as f:
            f.write(request.body)

        session.received_chunks += 1
        session.save(update_fields=["received_chunks"])

        return Response({"message": f"Чанк {chunk_index} загружен"})


class ChunkCompleteAPIView(APIView):
    permission_classes = [IsAdminOrSuperUserRole]

    """
    3️⃣ Завершение загрузки, склейка и сохранение файла в модель File
    """
    def post(self, request):
        upload_id = request.data.get("upload_id")
        file_name = request.data.get("file_name", "merged_file.bin")

        if not upload_id:
            return JsonResponse({"error": "upload_id обязателен"}, status=400)

        session = FileUploadSession.objects.filter(upload_id=upload_id, is_complete=False).first()
        if not session:
            return JsonResponse({"error": "Сессия не найдена или уже завершена"}, status=404)

        upload_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads", upload_id)
        if not os.path.exists(upload_dir):
            return JsonResponse({"error": "временные чанки не найдены"}, status=404)

        # 🔹 Сортировка chunk_0, chunk_1, ...
        chunk_files = sorted(
            [f for f in os.listdir(upload_dir) if f.startswith("chunk_")],
            key=lambda x: int(x.split("_")[-1])
        )
        if not chunk_files:
            return JsonResponse({"error": "чанков нет"}, status=400)

        # 🔹 Путь финального файла
        final_name = f"{uuid.uuid4().hex}_{file_name}"
        final_dir = os.path.join(settings.MEDIA_ROOT, "uploads", timezone.now().strftime("%Y/%m/%d"))
        os.makedirs(final_dir, exist_ok=True)
        final_path = os.path.join(final_dir, final_name)

        # 🔹 Склейка
        with open(final_path, "wb") as outfile:
            for chunk in chunk_files:
                with open(os.path.join(upload_dir, chunk), "rb") as infile:
                    outfile.write(infile.read())

        # 🔹 Очистка временных файлов
        for chunk in chunk_files:
            os.remove(os.path.join(upload_dir, chunk))
        os.rmdir(upload_dir)

        # 🔹 MIME-тип
        mime_type, _ = mimetypes.guess_type(final_path)
        file_type = "other"
        if mime_type:
            if mime_type.startswith("audio"):
                file_type = "audio"
            elif mime_type.startswith("video"):
                file_type = "video"
            elif mime_type.startswith("image"):
                file_type = "image"
            elif mime_type in ["application/pdf", "text/plain"]:
                file_type = "document"

        # 🔹 Создание записи в модели File
        file_obj = File.objects.create(
            folder=session.folder,
            name=file_name,
            file=os.path.relpath(final_path, settings.MEDIA_ROOT),
            file_type=file_type,
            size=os.path.getsize(final_path),
        )

        # 🔹 Завершаем сессию
        session.is_complete = True
        session.save(update_fields=["is_complete"])

        return JsonResponse({
            "message": "✅ Файл успешно загружен и сохранён",
            "file_id": str(file_obj.id),
            "file_type": file_type,
            "file_url": f"/media/{file_obj.file}",
        })


# ==============================
# 🔹 Просмотр файла по токену
# ==============================
class FileViewByTokenAPIView(APIView):

    """Просмотр файла по токену"""
    def get(self, request, token):
        try:
            file = File.objects.get(token=token)
        except File.DoesNotExist:
            return Response({'error': 'File not found'}, status=404)

        data = FileSerializer(file).data
        data['view_url'] = request.build_absolute_uri()
        data['download_url'] = request.build_absolute_uri(file.file.url if file.file else static('no_file.png'))
        return Response(data)


# ==============================
# 🔹 Замена файла без смены токена
# ==============================
class FileReplaceAPIView(APIView):
    permission_classes = [IsAdminOrSuperUserRole]

    """Заменяет файл, не трогая токен"""
    def put(self, request, pk):
        try:
            file = File.objects.get(pk=pk)
        except File.DoesNotExist:
            return Response({'error': 'File not found'}, status=404)

        new_file = request.FILES.get('file')
        if not new_file:
            return Response({'error': 'No file provided'}, status=400)

        file.file.delete(save=False)
        file.file = new_file
        file.name = new_file.name
        file.size = getattr(new_file, "size", None)
        file.save()

        return Response(FileSerializer(file).data)


class FileStreamAPIView(APIView):
    """Отдаёт файл с корректным Content-Type"""
    permission_classes = [IsAdminOrSuperUserRole]

    def get(self, request):
        files = File.objects.select_related('folder').order_by('-created_at')
        serializer = FileSerializer(files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FileMoveAPIView(APIView):
    permission_classes = [IsAdminOrSuperUserRole]

    """Перемещение файла в другую папку по токену папки"""

    def put(self, request):
        file_id = request.data.get("file_id")        # id или uuid файла
        folder_token = request.data.get("folder_token")  # токен папки назначения

        if not file_id or not folder_token:
            return Response({"error": "file_id и folder_token обязательны"}, status=400)

        try:
            file = File.objects.get(id=file_id)
        except File.DoesNotExist:
            return Response({"error": "Файл не найден"}, status=404)

        try:
            folder = Folder.objects.get(token=folder_token)
        except Folder.DoesNotExist:
            return Response({"error": "Папка не найдена"}, status=404)

        file.folder = folder
        file.save(update_fields=["folder"])

        return Response({
            "message": f"Файл {file.name} перемещён в папку {folder.name}",
            "file": FileSerializer(file).data
        })
