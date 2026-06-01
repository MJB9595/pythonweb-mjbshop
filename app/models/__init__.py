from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import certifi
from app.config import MONGODB_DB_NAME, MONGODB_URI


class MongoDB:
    def __init__(self):
        self.client = None
        self.engine = None

    def connect(self):
        if self.engine is not None:
            return  # 이미 연결됨
        self.client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
        self.engine = AIOEngine(client=self.client, database=MONGODB_DB_NAME)
        print("성공적으로 연결 되었습니다.")

    def get_engine(self) -> AIOEngine:
        """첫 호출 시 자동으로 연결 (Vercel 서버리스 대응)."""
        self.connect()
        return self.engine

    def close(self):
        if self.client:
            self.client.close()


mongodb = MongoDB()
