# 가령: 260422: 수정 내용 - 문장↔단어 매핑(LessonWordMapping) 시드/조회용 repository 신규 추가
from abc import ABC, abstractmethod
from typing import List

from fastapi import Depends
from sqlmodel import Session, select

from main.core.database import get_db
from main.domain.LessonWordMapping.entity.lesson_word_mapping import LessonWordMapping


class LessonWordMappingRepository(ABC):
    @abstractmethod
    def save(self, mapping: LessonWordMapping) -> LessonWordMapping:
        pass

    @abstractmethod
    def delete_by_sentence_id(self, sentence_lesson_id: int) -> int:
        pass

    @abstractmethod
    def find_by_sentence_id(self, sentence_lesson_id: int) -> List[LessonWordMapping]:
        pass


class SqlLessonWordMappingRepository(LessonWordMappingRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, mapping: LessonWordMapping) -> LessonWordMapping:
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def delete_by_sentence_id(self, sentence_lesson_id: int) -> int:
        existing = self.find_by_sentence_id(sentence_lesson_id)
        for m in existing:
            self.db.delete(m)
        self.db.commit()
        return len(existing)

    def find_by_sentence_id(self, sentence_lesson_id: int) -> List[LessonWordMapping]:
        statement = (
            select(LessonWordMapping)
            .where(LessonWordMapping.sentence_lesson_id == sentence_lesson_id)
            .order_by(LessonWordMapping.word_order)
        )
        return list(self.db.execute(statement).scalars().all())


def get_lesson_word_mapping_repository(
    db: Session = Depends(get_db),
) -> LessonWordMappingRepository:
    return SqlLessonWordMappingRepository(db)
