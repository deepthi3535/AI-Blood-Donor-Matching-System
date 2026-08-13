from app import db
from app.models.hospital import Hospital


def create_hospital(data):

    hospital = Hospital(**data)

    db.session.add(hospital)
    db.session.commit()

    return hospital


def get_all_hospitals():

    return Hospital.query.all()


def get_hospital(hospital_id):

    return Hospital.query.get(hospital_id)


def update_hospital(hospital, data):

    for key, value in data.items():
        setattr(hospital, key, value)

    db.session.commit()

    return hospital


def delete_hospital(hospital):

    db.session.delete(hospital)

    db.session.commit()