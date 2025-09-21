from sqlalchemy.orm import Session
import models
import datetime


def get_user_by_spotify_id(db: Session, spotify_id: str):
    return db.query(models.User).filter(models.User.spotify_id == spotify_id).first()


def create_user(db: Session, spotify_id: str, display_name: str, profile_pic_url: str | None):
    # Check if this is the first user. If so, make them an admin.
    user_count = db.query(models.User).count()
    is_first_user = user_count == 0

    db_user = models.User(
        spotify_id=spotify_id,
        display_name=display_name,
        profile_pic_url=profile_pic_url,
        is_admin=is_first_user,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_or_update_token(
    db: Session,
    user_id: int,
    access_token: str,
    refresh_token: str,
    expires_at: datetime.datetime,
):
    db_token = db.query(models.Token).filter(models.Token.user_id == user_id).first()
    if db_token:
        db_token.access_token = access_token
        db_token.refresh_token = refresh_token
        db_token.expires_at = expires_at
    else:
        db_token = models.Token(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def start_sharing(db: Session, user_id: int):
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    db_active_share = models.ActiveShare(user_id=user_id, expires_at=expires_at)
    db.add(db_active_share)
    db.commit()
    db.refresh(db_active_share)
    return db_active_share


def stop_sharing(db: Session, user_id: int):
    db.query(models.ActiveShare).filter(models.ActiveShare.user_id == user_id).delete()
    db.commit()


def get_feed(db: Session):
    feed_items = []
    active_shares = db.query(models.ActiveShare).filter(models.ActiveShare.expires_at > datetime.datetime.utcnow()).all()
    for share in active_shares:
        user = share.user
        track = user.track
        if track:
            feed_items.append(
                models.TrackFeedItem(
                    user_id=user.spotify_id,
                    display_name=user.display_name,
                    spotify_profile_pic=user.profile_pic_url,
                    current_track=f"{track.track_name} by {track.artist_name}",
                    album_cover=track.album_cover_url,
                    spotify_link=track.spotify_track_url,
                    currently_playing=track.currently_playing,
                )
            )
    return feed_items


def get_active_shares(db: Session):
    return db.query(models.ActiveShare).filter(models.ActiveShare.expires_at > datetime.datetime.utcnow()).all()


# --- Settings CRUD ---

def get_setting(db: Session, key: str):
    return db.query(models.Settings).filter(models.Settings.key == key).first()

def set_setting(db: Session, key: str, value: str):
    db_setting = get_setting(db, key)
    if db_setting:
        db_setting.value = value
    else:
        db_setting = models.Settings(key=key, value=value)
        db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


def get_token_by_user_id(db: Session, user_id: int):
    return db.query(models.Token).filter(models.Token.user_id == user_id).first()


def create_or_update_track(db: Session, user_id: int, track_data: dict):
    db_track = db.query(models.Track).filter(models.Track.user_id == user_id).first()
    if db_track:
        db_track.track_name = track_data["track_name"]
        db_track.artist_name = track_data["artist_name"]
        db_track.album_cover_url = track_data["album_cover_url"]
        db_track.spotify_track_url = track_data["spotify_track_url"]
        db_track.currently_playing = track_data["currently_playing"]
    else:
        db_track = models.Track(user_id=user_id, **track_data)
        db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track
