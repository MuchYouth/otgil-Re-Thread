from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import secrets
import string

from app import models, schemas


# --- 유틸리티 함수 ---

def generate_invite_code(length: int = 6) -> str:
    """
    6자리의 (대문자 + 숫자) 초대 코드를 생성합니다.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


# --- CRUD 함수 ---

def get_party(db: Session, party_id: str) -> Optional[models.Party]:
    """
    ID로 단일 파티를 조회합니다. (참가자 정보 포함)
    """
    return db.query(models.Party).filter(models.Party.id == party_id).first()


def get_party_by_invitation_code(db: Session, code: str) -> Optional[models.Party]:
    """
    초대 코드로 단일 파티를 조회합니다.
    """
    return db.query(models.Party).filter(models.Party.invitation_code == code).first()


def get_parties(
        db: Session,
        status: str,
        search: Optional[str] = None
) -> List[models.Party]:
    """
    특정 상태(status)의 파티 목록을 조회하며, 검색(search)을 지원합니다.
    """
    # 1. 상태(status)를 기준으로 기본 쿼리
    query = db.query(models.Party).filter(models.Party.status == status)

    # 2. 검색어가 있는 경우, 제목(title) 또는 설명(description)에서 검색
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Party.title.ilike(search_term),
                models.Party.description.ilike(search_term)
            )
        )

    # 3. 님의 스키마에 `date` 필드가 있으므로 `date` 기준으로 정렬
    return query.order_by(models.Party.date.desc()).all()


def create_party(db: Session, party: schemas.PartyCreate, host_id: str) -> models.Party:
    """
    새로운 파티를 생성합니다.
    - PENDING_APPROVAL 상태로 설정됩니다.
    - 고유한 초대 코드를 생성합니다.
    - 호스트를 'ACCEPTED' 상태의 첫 번째 참가자로 자동 추가합니다.
    """

    # 1. 초대 코드 생성
    invite_code = generate_invite_code()

    # 2. Party 모델 객체 생성
    db_party = models.Party(
        **party.model_dump(),
        host_id=host_id,
        status=schemas.PartyStatusEnum.PENDING_APPROVAL.value,
        invitation_code=invite_code
    )

    db.add(db_party)
    db.commit()
    db.refresh(db_party)

    # 3. 호스트를 참가자로 추가
    # host_id로 User 모델을 조회하여 nickname을 가져옵니다.
    host_user = db.query(models.User).filter(models.User.id == host_id).first()
    if host_user:
        add_participant(
            db,
            party_id=db_party.id,
            user_id=host_id,
            nickname=host_user.nickname,
            status=schemas.PartyParticipantStatusEnum.ACCEPTED  # 호스트는 자동 승인
        )

    db.refresh(db_party)  # 참가자 관계를 새로고침
    return db_party


def add_participant(
        db: Session,
        party_id: str,
        user_id: str,
        nickname: str,
        status: schemas.PartyParticipantStatusEnum = schemas.PartyParticipantStatusEnum.PENDING
) -> models.PartyParticipant:
    """
    파티에 참가자를 추가합니다.
    - 기본 상태는 'PENDING' (참가 신청)입니다.
    """

    # [방어 로직] 이미 참가자인지 확인
    existing = db.query(models.PartyParticipant).filter(
        models.PartyParticipant.party_id == party_id,
        models.PartyParticipant.user_id == user_id
    ).first()
    if existing:
        return existing

    db_participant = models.PartyParticipant(
        user_id=user_id,
        party_id=party_id,
        nickname=nickname,
        status=status.value
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant


def get_participants(db: Session, party_id: str) -> List[models.PartyParticipant]:
    """
    특정 파티의 모든 참가자 목록을 조회합니다.
    """
    return db.query(models.PartyParticipant).filter(models.PartyParticipant.party_id == party_id).all()


def remove_participant(
        db: Session,
        party_id: str,
        user_id: str
) -> Optional[models.PartyParticipant]:
    """
    파티에서 특정 참가자를 제거합니다. (호스트가 내보내거나, 본인이 나갈 때 사용)
    """
    db_participant = db.query(models.PartyParticipant).filter(
        models.PartyParticipant.party_id == party_id,
        models.PartyParticipant.user_id == user_id
    ).first()

    if db_participant:
        db.delete(db_participant)
        db.commit()
        return db_participant

    return None


def update_party(
        db: Session,
        db_party: models.Party,
        party_in: schemas.PartyUpdate
) -> models.Party:
    """
    파티 정보를 수정합니다. (제목, 설명, 상태 등)
    `PartyUpdate` 스키마에 정의된 (None이 아닌) 값들만 업데이트합니다.
    """
    # Pydantic v2: .model_dump(exclude_unset=True)
    update_data = party_in.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        # Enum 값은 .value로 문자열을 꺼내서 저장
        if isinstance(value, schemas.PartyStatusEnum):
            setattr(db_party, key, value.value)
        else:
            setattr(db_party, key, value)

    db.add(db_party)
    db.commit()
    db.refresh(db_party)
    return db_party


def get_parties_for_user(db: Session, user_id: str) -> List[models.Party]:
    """
    특정 유저가 '호스트'이거나 '참가'한 모든 파티 목록을 조회합니다.
    """
    # PartyParticipant 테이블과 JOIN하여 user_id가 일치하는 파티를 찾습니다.
    # (호스트는 create_party 시점에 참가자로 자동 추가되므로,
    # PartyParticipant 테이블만 조회해도 호스팅/참가 목록을 모두 얻을 수 있습니다.)
    query = db.query(models.Party) \
        .join(models.PartyParticipant, models.PartyParticipant.party_id == models.Party.id) \
        .filter(models.PartyParticipant.user_id == user_id) \
        .distinct()

    return query.order_by(models.Party.date.desc()).all()


def update_status(
        db: Session,
        db_party: models.Party,
        new_status: schemas.PartyStatusEnum
) -> models.Party:
    """
    (관리자용) 파티의 상태를 강제로 변경합니다.
    (참고: update_party 함수와 기능이 중복되지만, 관리자 라우터에서 명시적으로 호출)
    """
    db_party.status = new_status.value
    db.add(db_party)
    db.commit()
    db.refresh(db_party)
    return db_party