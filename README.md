# 📡 StreamVault Storage API Documentation

Информационная система хранения аудио- и видео-материалов. Ниже приведены все доступные REST API эндпоинты с примерами успешных запросов и ответов.

**Base URL:** `http://217.16.19.200`

---

## 🚀 Chunk Upload API

### 🔹 1. Инициализация загрузки чанков

**POST** `/storage/api/v3/chunk_init/`

**Request:**

```json
{
  "file_name": "example.mp4",
  "total_chunks": 5
}
```

**Response:**

```json
{
  "upload_id": "b32fb588-576f-42aa-8b91-32b477ccc4a1",
  "message": "Upload session initialized successfully"
}
```

---

### 🔹 2. Загрузка чанка файла

**POST** `/storage/api/v3/chunk_upload/`

**Request (FormData):**

```
upload_id: b32fb588-576f-42aa-8b91-32b477ccc4a1
chunk_number: 1
file: <binary>
```

**Response:**

```json
{
  "message": "Chunk 1 uploaded successfully"
}
```

---

### 🔹 3. Завершение загрузки файла

**POST** `/storage/api/v3/chunk_complete/`

**Request:**

```json
{
  "upload_id": "b32fb588-576f-42aa-8b91-32b477ccc4a1"
}
```

**Response:**

```json
{
  "file_id": 15,
  "file_name": "example.mp4",
  "message": "File successfully assembled"
}
```

---

## 📁 Folder Management

### 🔹 4. Создание папки

**POST** `/storage/api/v3/folders/`

**Request:**

```json
{
  "name": "Music",
  "description": "My favorite tracks"
}
```

**Response:**

```json
{
  "id": 1,
  "name": "Music",
  "token": "e4b1a8d7-5a21-4a32-a1c9-3e2b1a0c3f54",
  "message": "Folder created successfully"
}
```

---

### 🔹 5. Обновление папки

**PUT** `/storage/api/v3/folders/update/`

**Request:**

```json
{
  "token": "e4b1a8d7-5a21-4a32-a1c9-3e2b1a0c3f54",
  "name": "Music Updated",
  "description": "Updated folder description"
}
```

**Response:**

```json
{
  "message": "Folder updated successfully"
}
```

---

### 🔹 6. Просмотр папки по токену

**GET** `/storage/api/v3/folders/<token>/`

**Response:**

```json
{
  "id": 1,
  "name": "Music Updated",
  "description": "Updated folder description",
  "files": []
}
```

---

## 🎞 File Management

### 🔹 7. Просмотр файла по токену

**GET** `/storage/api/v3/files/<token>/`

**Response:**

```json
{
  "id": 12,
  "file_name": "example.mp4",
  "folder": "Music",
  "size": "23 MB",
  "created_at": "2025-10-18T17:42:11Z"
}
```

---

### 🔹 8. Замена файла

**PUT** `/storage/api/v3/files/replace/<id>/`

**Request (FormData):**

```
file: <binary>
```

**Response:**

```json
{
  "message": "File replaced successfully"
}
```

---

### 🔹 9. Перемещение файла в другую папку

**POST** `/storage/api/v3/files_move/`

**Request:**

```json
{
  "file_id": 12,
  "folder_token": "e4b1a8d7-5a21-4a32-a1c9-3e2b1a0c3f54"
}
```

**Response:**

```json
{
  "message": "File moved successfully"
}
```

---

### 🔹 10. Получить список всех файлов

**GET** `/storage/api/v3/all_files/`

**Response:**

```json
[
  {
    "id": 12,
    "file_name": "example.mp4",
    "folder": "Music",
    "size": "23 MB"
  },
  {
    "id": 13,
    "file_name": "song.mp3",
    "folder": "Audio",
    "size": "8 MB"
  }
]
```

---

## 🔗 QR Codes

### 🔹 11. Генерация QR-кода по токену

**GET** `/storage/api/v3/qr/<token>/`

**Response:**

```json
{
  "qr_url": "http://217.16.19.200/storage/media/qr/folder_qr.png"
}
```

---

## 👤 Authentication API

### 🔹 12. Регистрация пользователя

**POST** `/storage/api/v5/register/`

**Request:**

```json
{
  "email": "user@example.com",
  "username": "user1",
  "password": "securePassword123"
}
```

**Response:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user1",
  "message": "User registered successfully"
}
```

---

### 🔹 13. Авторизация пользователя

**POST** `/storage/api/v5/login/`

**Request:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login successful"
}
```

---

### 🔹 14. Информация о текущем пользователе

**GET** `/storage/api/v5/me/`

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user1",
  "date_joined": "2025-10-18T15:45:31Z"
}
```

---

# Streamvault API Documentation (Files & Folders)

Данная документация описывает работу с эндпоинтами для редактирования и удаления файлов и папок в проекте **Streamvault**.

---

## 📂 Файлы

### 1️⃣ Редактирование файла

**Endpoint:**  


**Описание:**  
Позволяет изменить имя файла или переместить его в другую папку.  
PUT /api/v4/files/<uuid:pk>/update/
**Request Body (JSON):**
```json
{
  "name": "new_file_name.mp3",   // новое имя файла
  "folder": "<uuid_папки>"       // (необязательно) новая папка
}
```
```
{
  "id": "file_uuid",
  "name": "new_file_name.mp3",
  "token": "file_token",
  "file_type": "audio",
  "folder": "folder_uuid",
  "file": "uploads/2025/10/19/file_uuid_new_file_name.mp3",
  "size": 1048576
}
```

DELETE /api/v4/files/<uuid:pk>/delete/

```
{
  "message": "Файл успешно удалён"
}
```

PUT /api/v4/folders/<uuid:pk>/update/

```
{
  "name": "New Folder Name",       // новое имя папки
  "parent": "<uuid_родительской_папки или null>"  // родительская папка
}

```

```
{
  "id": "folder_uuid",
  "name": "New Folder Name",
  "token": "folder_token",
  "parent": "parent_folder_uuid_or_null"
}
```

Удаление папки

Endpoint:
DELETE /api/v4/folders/<uuid:pk>/delete/

```
{
  "message": "Папка и все вложения успешно удалены"
}
```






## 🧩 Примечания

* Все запросы поддерживают формат `application/json`, кроме загрузки файлов (`multipart/form-data`).
* Эндпоинты `/api/v5/*` используют JWT-аутентификацию (через библиотеку SimpleJWT).
* Пример базового URL можно заменить на `{{base_url}}` для использования в Postman коллекции.

---

📄 **Автор:** Aspandiyar Dossov
🗓 **Последнее обновление:** 2025-10-19
