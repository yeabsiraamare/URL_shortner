```markdown
# Django URL Shortener API

A complete URL shortening service built with Django and PostgreSQL. Create short links, track analytics, and manage URLs through a RESTful API.

## 🎯 What This Project Does

This is a backend API service that:
1. **Shortens long URLs** - Converts `https://example.com/very-long-path` to `http://yoursite.com/abc123`
2. **Tracks clicks** - Records every time someone clicks your short link
3. **Provides analytics** - Shows where clicks came from, what devices were used, when they clicked
4. **Auto-expires links** - Links stop working after 30 days (or your chosen time)
5. **No login required** - Each URL has a secret key for management

## 📦 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- pip package manager

### Step 1: Setup PostgreSQL

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE urlshortener;
CREATE USER urluser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE urlshortener TO urluser;

# Exit PostgreSQL
\q
```

### Step 2: Setup Project

```bash
# Clone/download the project
cd url-shortener-project

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env file with your database credentials

# Setup database
python manage.py migrate

# Create admin user (optional, for /admin interface)
python manage.py createsuperuser

# Run server
python manage.py runserver
```

Your API is now running at `http://localhost:8000/`

## 🚀 How to Use the API

### 1. Create a Short URL

When you have a long URL you want to shorten:

```bash
curl -X POST http://localhost:8000/api/urls/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://github.com/very-long-repository-path",
    "expires_in": 30
  }'
```

**Response:**
```json
{
  "short_url": "http://localhost:8000/abc123",
  "stats_url": "http://localhost:8000/api/urls/stats/?code=abc123&admin_key=xyz789",
  "admin_key": "xyz789abc123def456",
  "expires_in": 30,
  "expires_at": "2024-12-30T10:00:00Z",
  "short_code": "abc123"
}
```

**Save the `admin_key`!** You need it to view stats or delete the URL.

### 2. Use the Short URL

Share the `short_url` with others. When they click it:

```bash
# In browser: Visit http://localhost:8000/abc123
# Or with curl:
curl -L http://localhost:8000/abc123
```

What happens:
- User is redirected to the original GitHub URL
- A "click" is recorded in the database
- Analytics data is saved (device, browser, time, etc.)

### 3. View Analytics

To see how many people clicked your link:

```bash
# Use the code and admin_key from step 1
curl "http://localhost:8000/api/urls/stats/?code=abc123&admin_key=xyz789abc123def456"
```

**Response shows:**
- Total number of clicks
- Clicks per day
- Device types (mobile/desktop/tablet)
- Browsers used
- Locations (if available)
- Recent clicks with timestamps

### 4. Delete a URL

When you no longer need the short URL:

```bash
curl -X DELETE "http://localhost:8000/api/urls/delete/?code=abc123&admin_key=xyz789abc123def456"
```

## 🧪 Complete Testing Example

Here's a full workflow to test everything:

```bash
# 1. Create a URL for testing
RESPONSE=$(curl -s -X POST http://localhost:8000/api/urls/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/get"}')

# Extract the short code and admin key
SHORT_CODE=$(echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['short_url'].split('/')[-1])")
ADMIN_KEY=$(echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['admin_key'])")

echo "Created: http://localhost:8000/$SHORT_CODE"
echo "Admin Key: $ADMIN_KEY"

# 2. Click it 3 times (simulate users)
for i in {1..3}; do
  echo "Click $i..."
  curl -s -o /dev/null -L http://localhost:8000/$SHORT_CODE
done

# 3. Check analytics
echo "Checking analytics..."
curl -s "http://localhost:8000/api/urls/stats/?code=$SHORT_CODE&admin_key=$ADMIN_KEY" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total clicks: {d[\"total_clicks\"]}')"

# Should show: Total clicks: 3

# 4. Clean up
curl -X DELETE "http://localhost:8000/api/urls/delete/?code=$SHORT_CODE&admin_key=$ADMIN_KEY"
echo "Test completed and cleaned up!"
```

## 📊 What Data is Tracked

For each click, the system records:
- **When**: Timestamp of click
- **Where from**: IP address (anonymized)
- **What device**: Mobile, desktop, or tablet
- **What browser**: Chrome, Firefox, Safari, etc.
- **Referrer**: Which site brought them here
- **Location**: Country and city (from IP)

## 🔧 API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/urls/` | Create new short URL |
| GET | `/{short_code}/` | Redirect to original URL |
| GET | `/api/urls/stats/?code=X&admin_key=Y` | Get analytics for a URL |
| DELETE | `/api/urls/delete/?code=X&admin_key=Y` | Delete a URL |

## 🐛 Troubleshooting

### "Database connection failed"
- Make sure PostgreSQL is running: `brew services start postgresql` (Mac) or `sudo service postgresql start` (Linux)
- Check credentials in `.env` file match what you created in PostgreSQL

### "404 Not Found"
- Make sure server is running: `python manage.py runserver`
- Check endpoint URL is correct

### "500 Internal Server Error"
- Check the terminal where server is running for error details
- Might be missing packages: run `pip install -r requirements.txt`

### "Invalid URL"
- Make sure URL starts with `http://` or `https://`
- URL must be valid and accessible

## 🧪 Running Tests

The project includes comprehensive tests:

```bash
# Run all tests
python manage.py test

# Run specific test files
python manage.py test tests.test_models
python manage.py test tests.test_views

# See test details
python manage.py test --verbosity=2
```

