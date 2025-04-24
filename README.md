# Move Dashboard

A Dash application for tracking and managing moves.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```
5. Run the application:
   ```bash
   python item_planning.py
   ```

## Environment Variables

- `PORT`: Port to run the application on (default: 8051)
- `ANDY_PASSWORD`: Password for user 'andy'
- `LUCIA_PASSWORD`: Password for user 'lucia'
- `ADMIN_PASSWORD`: Password for admin user

## Database

The application uses SQLite, stored in the `data/` directory.

## Deployment

See deployment instructions in `DEPLOYMENT.md`.
