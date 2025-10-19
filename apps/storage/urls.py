from django.urls import path
from .views import (
    ChunkInitAPIView, ChunkUploadAPIView, ChunkCompleteAPIView, FolderCreateAPIView, FolderUpdateAPIView,
    FolderViewByTokenAPIView, FileViewByTokenAPIView, FileReplaceAPIView, QRCodeAPIView,
    FileStreamAPIView, FileMoveAPIView, RegisterView, LoginView, UserDetailView, FileUpdateAPIView,
    FileDeleteAPIView, FolderDeleteAPIView, RootFoldersAPIView
)

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView


urlpatterns = [
    # Базовые операции

    # Chunk upload
    path("api/v3/chunk_init/", ChunkInitAPIView.as_view(), name="chunk-init"),
    path("api/v3/chunk_upload/", ChunkUploadAPIView.as_view(), name="chunk-upload"),
    path("api/v3/chunk_complete/", ChunkCompleteAPIView.as_view(), name="chunk-complete"),


    # Folders
    path("api/v3/folders/", FolderCreateAPIView.as_view(), name="folder-create"),
    path("api/v3/folders/update/", FolderUpdateAPIView.as_view(), name="folder-update"),
    path("api/v3/folders/<str:token>/", FolderViewByTokenAPIView.as_view(), name="folder-view"),

    # Files
    path("api/v3/files/<str:token>/", FileViewByTokenAPIView.as_view(), name="file-view"),
    path("api/v3/files/replace/<int:pk>/", FileReplaceAPIView.as_view(), name="file-replace"),

    # QR
    path("api/v3/qr/<str:token>/", QRCodeAPIView.as_view(), name="generate-qr"),

    # Добавить файл (после создание с чанками) в нужную папку
    path("api/v3/files_move/", FileMoveAPIView.as_view(), name="file-move"),

    path("api/v3/all_files/", FileStreamAPIView.as_view(), name="file-stream"),

    # Registration and Login
    path("api/v5/register/", RegisterView.as_view(), name="register"),
    path("api/v5/login/", LoginView.as_view(), name="login"),
    path("api/v5/me/", UserDetailView.as_view(), name="user-detail"),

    # JWT стандартные эндпоинты
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    path("files/<uuid:pk>/update/", FileUpdateAPIView.as_view(), name="file-update"),
    path("files/<uuid:pk>/delete/", FileDeleteAPIView.as_view(), name="file-delete"),
    path("folders/<uuid:pk>/update/", FolderUpdateAPIView.as_view(), name="folder-update"),
    path("folders/<uuid:pk>/delete/", FolderDeleteAPIView.as_view(), name="folder-delete"),

    path("api/v4/folders_root/", RootFoldersAPIView.as_view(), name="folders-root"),

]
