"""
SQLite to PostgreSQL Migration Script
기존 SQLite 데이터베이스의 데이터를 PostgreSQL로 마이그레이션합니다.
"""
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def migrate_database(
    sqlite_path: str = "data/database/quant_investing.db",
    pg_host: str = "localhost",
    pg_port: int = 5432,
    pg_database: str = "quant_investing",
    pg_user: str = "postgres",
    pg_password: str = "postgres"
):
    """
    SQLite 데이터베이스를 PostgreSQL로 마이그레이션합니다.

    Args:
        sqlite_path: SQLite 데이터베이스 파일 경로
        pg_host: PostgreSQL 호스트
        pg_port: PostgreSQL 포트
        pg_database: PostgreSQL 데이터베이스 이름
        pg_user: PostgreSQL 사용자
        pg_password: PostgreSQL 비밀번호
    """
    sqlite_full_path = project_root / sqlite_path

    if not sqlite_full_path.exists():
        print(f"SQLite 데이터베이스 파일을 찾을 수 없습니다: {sqlite_full_path}")
        return False

    print(f"SQLite 데이터베이스: {sqlite_full_path}")
    print(f"PostgreSQL: {pg_user}@{pg_host}:{pg_port}/{pg_database}")

    # SQLite 연결
    sqlite_conn = sqlite3.connect(sqlite_full_path)

    # PostgreSQL 연결
    pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    pg_engine = create_engine(pg_connection_string)

    # 마이그레이션할 테이블 목록
    tables = [
        'stock_prices',
        'stock_fundamentals',
        'stock_info',
        'strategy_results',
        'portfolio_holdings',
        'background_tasks'
    ]

    print("\n=== 마이그레이션 시작 ===\n")

    for table in tables:
        try:
            # SQLite에서 데이터 읽기
            df = pd.read_sql(f"SELECT * FROM {table}", sqlite_conn)

            if df.empty:
                print(f"[SKIP] {table}: 데이터 없음")
                continue

            print(f"[READ] {table}: {len(df)} 행")

            # PostgreSQL에 데이터 쓰기
            df.to_sql(table, pg_engine, if_exists='append', index=False)

            print(f"[DONE] {table}: {len(df)} 행 마이그레이션 완료")

        except Exception as e:
            print(f"[ERROR] {table}: {str(e)}")
            continue

    # 연결 종료
    sqlite_conn.close()
    pg_engine.dispose()

    print("\n=== 마이그레이션 완료 ===")
    return True


def migrate_web_database(
    sqlite_path: str = "data/database/web_app.db",
    pg_host: str = "localhost",
    pg_port: int = 5432,
    pg_database: str = "quant_web",
    pg_user: str = "postgres",
    pg_password: str = "postgres"
):
    """
    웹 애플리케이션 SQLite 데이터베이스를 PostgreSQL로 마이그레이션합니다.
    """
    sqlite_full_path = project_root / sqlite_path

    if not sqlite_full_path.exists():
        print(f"웹 앱 SQLite 데이터베이스 파일을 찾을 수 없습니다: {sqlite_full_path}")
        return False

    print(f"웹 앱 SQLite 데이터베이스: {sqlite_full_path}")
    print(f"PostgreSQL: {pg_user}@{pg_host}:{pg_port}/{pg_database}")

    # SQLite 연결
    sqlite_conn = sqlite3.connect(sqlite_full_path)

    # PostgreSQL 연결
    pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    pg_engine = create_engine(pg_connection_string)

    # SQLite에서 테이블 목록 가져오기
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]

    print(f"\n발견된 테이블: {tables}")
    print("\n=== 웹 앱 DB 마이그레이션 시작 ===\n")

    for table in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", sqlite_conn)

            if df.empty:
                print(f"[SKIP] {table}: 데이터 없음")
                continue

            print(f"[READ] {table}: {len(df)} 행")
            df.to_sql(table, pg_engine, if_exists='append', index=False)
            print(f"[DONE] {table}: {len(df)} 행 마이그레이션 완료")

        except Exception as e:
            print(f"[ERROR] {table}: {str(e)}")
            continue

    sqlite_conn.close()
    pg_engine.dispose()

    print("\n=== 웹 앱 DB 마이그레이션 완료 ===")
    return True


def create_postgresql_databases(
    pg_host: str = "localhost",
    pg_port: int = 5432,
    pg_user: str = "postgres",
    pg_password: str = "postgres"
):
    """
    PostgreSQL 데이터베이스들을 생성합니다.
    """
    from sqlalchemy import create_engine
    from sqlalchemy_utils import database_exists, create_database

    databases = ['quant_investing', 'quant_web', 'quant_web_test']

    for db_name in databases:
        url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{db_name}"
        try:
            if not database_exists(url):
                create_database(url)
                print(f"[CREATED] 데이터베이스 생성됨: {db_name}")
            else:
                print(f"[EXISTS] 데이터베이스 이미 존재: {db_name}")
        except Exception as e:
            print(f"[ERROR] {db_name} 생성 실패: {e}")
            print(f"  수동으로 생성하세요: CREATE DATABASE {db_name};")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SQLite to PostgreSQL Migration")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--user", default="postgres", help="PostgreSQL user")
    parser.add_argument("--password", default="postgres", help="PostgreSQL password")
    parser.add_argument("--create-db", action="store_true", help="Create databases first")
    parser.add_argument("--quant-only", action="store_true", help="Migrate only quant database")
    parser.add_argument("--web-only", action="store_true", help="Migrate only web database")

    args = parser.parse_args()

    print("=" * 50)
    print("SQLite to PostgreSQL Migration Tool")
    print("=" * 50)

    if args.create_db:
        print("\n>>> 데이터베이스 생성 중...")
        create_postgresql_databases(
            pg_host=args.host,
            pg_port=args.port,
            pg_user=args.user,
            pg_password=args.password
        )

    if not args.web_only:
        print("\n>>> Quant 데이터베이스 마이그레이션...")
        migrate_database(
            pg_host=args.host,
            pg_port=args.port,
            pg_database="quant_investing",
            pg_user=args.user,
            pg_password=args.password
        )

    if not args.quant_only:
        print("\n>>> 웹 앱 데이터베이스 마이그레이션...")
        migrate_web_database(
            pg_host=args.host,
            pg_port=args.port,
            pg_database="quant_web",
            pg_user=args.user,
            pg_password=args.password
        )

    print("\n" + "=" * 50)
    print("마이그레이션 프로세스 완료")
    print("=" * 50)
