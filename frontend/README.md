# Ondo Frontend

Next.js frontend for Ondo dataset readiness scoring.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

2. **Configure environment:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your API URL
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

## Project Structure

```
frontend/
├── app/
│   ├── api/
│   │   └── client.ts          # API client utilities
│   ├── datasets/
│   │   └── page.tsx           # Dataset list page
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Home page
│   └── globals.css            # Global styles
├── components/                # Reusable components (future)
└── public/                    # Static assets
```

## Features

### Dataset List Page (`/datasets`)

- **Table View**: Displays datasets with:
  - Dataset name (display name + full name)
  - Readiness score (0-100) with progress bar
  - Status badge (Gold, Production Ready, Internal, Draft)
  - Owner name
  - Last scored timestamp

- **Filters**:
  - Status filter (dropdown)
  - Owner filter (text input)
  - Search query (searches full_name and display_name)

- **Features**:
  - Clickable rows (navigate to detail page)
  - Loading states
  - Error handling
  - Responsive design

## API Integration

The frontend uses `fetch` to call the backend API:

- Base URL: `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`)
- Endpoint: `GET /api/datasets` with query parameters

## Development

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React 18** - UI library

