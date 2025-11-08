# Ciphare - Secure File Encryption & Sharing Platform

A secure web application for encrypting files and sharing them with time-limited, access-controlled links. Built with Next.js, Flask, MongoDB, and Cloudflare R2.

## Features

- **File Encryption**: Encrypt any file using AES-256 encryption
- **Time-Limited Storage**: Files are automatically deleted after a specified TTL (1 minute to 90 days)
- **Access Control**: Limit the number of times a file can be decrypted
- **Secure Sharing**: Generate unique, shareable links for encrypted files
- **Password Protection**: Files are encrypted with user-provided passwords
- **Community Posts**: Optional community feature for sharing encrypted posts

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend**: Flask (Python), serverless-wsgi
- **Database**: MongoDB Atlas (metadata) + Cloudflare R2 (file storage)
- **Encryption**: AES-256-GCM via Python cryptography library
- **Deployment**: Vercel, Railway, or Netlify

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- MongoDB Atlas account (free M0 tier)
- Cloudflare R2 account (free tier with 10GB storage)
- Deployment platform account (Vercel, Railway, or Netlify)

## Quick Start

For detailed setup instructions, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ciphare
```

### 2. Install dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=your-bucket-name

# Application Domain (for generating shareable links)
DOMAIN=http://localhost:3000

# CORS Origins (comma-separated, or * for all)
CORS_ORIGINS=*

# Flask Debug Mode
FLASK_DEBUG=True

# Next.js Public API Base URL (for local development)
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000
```

### 4. Run the development servers

```bash
# Run both Next.js and Flask servers concurrently
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Flask API: http://localhost:5328

## Production Deployment

This application can be deployed on multiple platforms. **Railway is recommended** for the best experience with Flask.

### 🚂 Railway (Recommended)

Railway is the best choice for this full-stack application. It can run Flask as a full service, providing better performance.

**Quick Start:**
- See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for detailed instructions
- Create two services: Frontend (Next.js) and Backend (Flask)
- Set environment variables and deploy!

**Why Railway?**
- ✅ Full Flask service (no serverless limitations)
- ✅ Better performance (no cold starts)
- ✅ Simpler setup
- ✅ See [DEPLOYMENT_COMPARISON.md](./DEPLOYMENT_COMPARISON.md) for details

### ☁️ Vercel

Vercel is great for Next.js and supports Python serverless functions.

**Quick Start:**
- See [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) for detailed instructions
- Configure environment variables in Vercel dashboard
- Deploy!

### 🌐 Netlify

Netlify works but requires additional setup. See [NETLIFY_DEPLOYMENT.md](./NETLIFY_DEPLOYMENT.md) for instructions.

### 📊 Platform Comparison

See [DEPLOYMENT_COMPARISON.md](./DEPLOYMENT_COMPARISON.md) for a detailed comparison.

---

## Production Deployment on Vercel

### 1. Prepare for deployment

1. Ensure all environment variables are set in your Vercel project settings
2. Make sure `vercel.json` is properly configured (already done)

### 2. Deploy to Vercel

```bash
# Install Vercel CLI if not already installed
npm i -g vercel

# Deploy
vercel

# For production deployment
vercel --prod
```

### 3. Configure Vercel Environment Variables

In your Vercel project settings, add the following environment variables:

- `MONGODB_URI`: Your MongoDB Atlas connection string
- `R2_ACCOUNT_ID`: Your Cloudflare R2 account ID
- `R2_ACCESS_KEY_ID`: Your Cloudflare R2 access key ID
- `R2_SECRET_ACCESS_KEY`: Your Cloudflare R2 secret access key
- `R2_BUCKET_NAME`: Your Cloudflare R2 bucket name
- `DOMAIN`: Your Vercel deployment URL (e.g., `https://your-app.vercel.app`)
- `CORS_ORIGINS`: Your production domain (or `*` for development)

### 4. Important Notes for Vercel Deployment

- Python serverless functions are automatically detected in the `api/` directory
- The `vercel.json` file configures routing for both Next.js and Python functions
- Each API endpoint (`/api/encode`, `/api/decode`, `/api/posts`) is a separate serverless function
- Functions use `serverless-wsgi` to wrap the Flask application

### 5. Storage Architecture

The application uses a hybrid storage approach:

- **MongoDB Atlas**: Stores file metadata (file_id, file_name, encryption keys, TTL, reads count)
- **Cloudflare R2**: Stores encrypted file data (up to 500MB per file)

**Why this architecture?**
- MongoDB free tier (512MB) is sufficient for metadata (thousands of files)
- R2 free tier (10GB) handles large encrypted files
- Separation of concerns: fast metadata queries + scalable file storage
- Cost-effective: Both services offer generous free tiers

## Project Structure

```
ciphare/
├── api/                    # Python Flask API
│   ├── encode/            # Encryption endpoint (serverless function)
│   │   └── index.py
│   ├── decode/            # Decryption endpoint (serverless function)
│   │   └── index.py
│   ├── posts/             # Posts API endpoint (serverless function)
│   │   └── index.py
│   ├── encryption/        # Encryption algorithms
│   │   ├── base.py
│   │   └── aes256.py
│   ├── app.py             # Main Flask application
│   ├── encode.py          # Encode blueprint
│   ├── decode.py          # Decode blueprint
│   ├── posts.py           # Posts blueprint
│   ├── registry.py        # Encryption algorithm registry
│   ├── storage.py         # MongoDB + R2 storage handler
│   └── utils.py           # Utility functions
├── src/                   # Next.js frontend
│   └── app/
│       ├── encode/        # Encryption page
│       ├── decode/        # Decryption page
│       ├── community/     # Community posts page
│       └── [compositeKey]/ # Dynamic route for file links
├── vercel.json            # Vercel configuration
├── next.config.ts         # Next.js configuration
├── requirements.txt       # Python dependencies
└── package.json          # Node.js dependencies
```

## Security Features

- **AES-256-GCM Encryption**: Industry-standard authenticated encryption
- **Password-based Key Derivation**: Uses Scrypt KDF for secure key derivation
- **Input Validation**: All inputs are validated and sanitized
- **Request Timeouts**: All external requests have timeouts to prevent hanging
- **CORS Configuration**: Configurable CORS for production security
- **File Size Limits**: Maximum 500MB file size
- **TTL Enforcement**: Automatic file deletion after expiration
- **Read Limits**: Files are deleted after reaching read limit

## API Endpoints

### POST `/api/encode`
Encrypt a file and store it in MongoDB (metadata) and R2 (encrypted file).

**Request Body:**
```json
{
  "file_data": "base64_encoded_file",
  "file_name": "example.txt",
  "file_type": "text/plain",
  "password": "user_password",
  "reads": 1,
  "ttl": 86400,
  "algorithm": "AES256"
}
```

**Response:**
```json
{
  "file_id": "unique_file_id",
  "share_link": "https://domain.com/decode/file_id"
}
```

### POST `/api/decode`
Decrypt a file using file ID and password.

**Request Body:**
```json
{
  "file_id": "unique_file_id",
  "password": "user_password",
  "algorithm": "AES256"
}
```

**Response:**
```json
{
  "decrypted_data": "base64_encoded_decrypted_file",
  "file_name": "example.txt",
  "file_type": "text/plain",
  "remaining_reads": 0
}
```

### GET `/api/posts`
Retrieve all community posts.

### POST `/api/posts`
Create a new community post.

## Troubleshooting

### Vercel Deployment Issues

1. **Python functions not working**: Ensure `serverless-wsgi` is in `requirements.txt`
2. **Environment variables not loading**: Check Vercel project settings
3. **CORS errors**: Verify `CORS_ORIGINS` environment variable
4. **Database/storage connection errors**: Verify MongoDB and R2 environment variables are set correctly

### Local Development Issues

1. **Port conflicts**: Change ports in `package.json` scripts if needed
2. **Python import errors**: Ensure you're in the correct directory and virtual environment
3. **Database/storage connection**: Verify your MongoDB Atlas and Cloudflare R2 credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.
