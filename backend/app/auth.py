"""Local operator recovery: python -m app.auth reset-password."""
import argparse
import getpass
from app.repositories.access_repository import AccessRepository
from app.services.access_service import hash_password


def main():
    parser = argparse.ArgumentParser(description='Recover an account without disabling user management')
    parser.add_argument('command', choices=['reset-password'])
    parser.parse_args()
    repo = AccessRepository()
    row = repo.user(username=input('Username: ').strip())
    if not row:
        parser.exit(1, 'Account not found. Protection has not changed.\n')
    password = getpass.getpass('New password (12–128 characters): ')
    if password != getpass.getpass('Confirm new password: '):
        parser.exit(1, 'Passwords do not match. No changes made.\n')
    repo.set_password(row['id'], hash_password(password))
    print('Password reset. Login sessions and account credentials revoked. User management remains enabled.')


if __name__ == '__main__':
    main()
