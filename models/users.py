import logging
logger = logging.getLogger(__name__)

from Configs import baseConfig

config = baseConfig()
recaptcha = config["RECAPTCHA"]
ENABLE_RECAPTCHA = recaptcha["ENABLE_RECAPTCHA"]
SECRET_KEY = recaptcha["SECRET_KEY"]

import requests

from peewee import DatabaseError

from schemas.users import Users
from schemas.usersinfo import UsersInfos

from security.data import Data

from werkzeug.exceptions import Unauthorized
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Conflict
from werkzeug.exceptions import InternalServerError

UserObject = ()

class User_Model:
    def __init__(self) -> None:
        """
        """
        self.Users = Users
        self.UsersInfos = UsersInfos
        self.Data = Data

    def create(self, phone_number: str, country_code: str, name: str, password: str) -> str:
        """
        """
        try:
            data = self.Data()
            full_phone_number = country_code+phone_number
            phone_number_hash = data.hash(data=full_phone_number)

            logger.debug("Finding verified userinfo: %s" % phone_number_hash)

            result = []

            userinfos = (
                self.UsersInfos.select()
                .where(
                    self.UsersInfos.full_phone_number == phone_number_hash,
                    self.UsersInfos.status == "verified"
                )
                .dicts()
            )

            for userinfo in userinfos:
                result.append(userinfo)

            # check for duplicate user
            if len(result) > 1:
                logger.error("Duplicate verified users found: %s" % phone_number_hash)
                raise Conflict()

            logger.info("- Successfully found verified users: %s" % phone_number_hash)

            # check for no user
            if len(result) < 1:
                logger.debug("creating user '%s' ..." % phone_number_hash)

                data = self.Data()
                password_hash = data.hash(password)

                new_user = self.Users.create(
                    password = password_hash
                )

                self.UsersInfos.create(
                    name = data.encrypt(data=name)["e_data"],
                    country_code = data.encrypt(data=country_code)["e_data"],
                    full_phone_number = phone_number_hash,
                    userId= new_user.id,
                    iv = data.iv
                )

                logger.info("- User '%s' successfully created" % phone_number_hash)
                return str(new_user.id)
            else:
                logger.error("user '%s' already has an acount" % phone_number_hash)
                raise Conflict()

        except DatabaseError as err:
            logger.error("creating user '%s' failed check logs" % full_phone_number)
            raise InternalServerError(err)

    def verify(self, password: str, phone_number: str = None, user_id: str = None) -> dict:
        """
        """
        try:
            data = self.Data()
            password_hash = data.hash(password)

            if phone_number:
                phone_number_hash = data.hash(phone_number)

                logger.debug("Verifying user: %s" % phone_number_hash)

                userinfos = (
                    self.UsersInfos.select()
                    .where(
                        self.UsersInfos.full_phone_number == phone_number_hash,
                        self.UsersInfos.status == "verified"
                    )
                    .dicts()
                )

                # check for no user
                if len(userinfos) < 1:
                    logger.error("Userinfo with Phone number '%s' not found" % phone_number_hash)
                    raise Unauthorized()

                # check for duplicate user
                if len(userinfos) > 1:
                    logger.error("Duplicate verified users found: %s" % phone_number_hash)
                    raise Conflict()

                logger.debug("Verifying password for user: %s" % phone_number_hash)

                users = (
                    self.Users.select()
                    .where(
                        self.Users.id == userinfos[0]["userId"],
                        self.Users.password == password_hash
                    )
                    .dicts()
                )

                # check for no user
                if len(users) < 1:
                    logger.error("Invalid password")
                    raise Unauthorized()

                # check for duplicate user
                if len(users) > 1:
                    logger.error("Duplicate users found: %s" % phone_number_hash)
                    raise Conflict()

                logger.info("- Successfully found verified user: %s" % phone_number_hash)
                return userinfos[0]

            elif user_id:
                logger.debug("Verifying user with id: %s" % user_id)

                users = (
                    self.Users.select()
                    .where(
                        self.Users.id == user_id,
                        self.Users.password == password_hash
                    )
                    .dicts()
                )

                # check for no user
                if len(users) < 1:
                    logger.error("User with Phone number '%s' not found" % phone_number_hash)
                    raise Unauthorized()

                # check for duplicate user
                if len(users) > 1:
                    logger.error("Duplicate users found: %s" % phone_number_hash)
                    raise Conflict()

                logger.info("- Successfully found verified user: %s" % phone_number_hash)
                return users[0]

        except DatabaseError as err:
            logger.error("Failed verifying user check logs")
            raise InternalServerError(err)


    # def find(self, table: str, phone_number: str = None, user_id: str = None, id: str = None) -> UserObject:
    #     """
    #     """
    #     try:
    #         if table == "userinfo":
    #             if phone_number:
    #                 logger.debug("Finding verified userinfo: %s" % phone_number)

    #                 result = []

    #                 userinfos = (
    #                     self.UsersInfos.select()
    #                     .where(
    #                         self.UsersInfos.full_phone_number == phone_number,
    #                         self.UsersInfos.status == "verified"
    #                     )
    #                     .dicts()
    #                 )

    #                 for userinfo in userinfos:
    #                     result.append(userinfo)

    #                 # check for no user
    #                 if len(result) < 1:
    #                     return None

    #                 # check for duplicate user
    #                 if len(result) > 1:
    #                     logger.error("Duplicate verified users found: %s" % phone_number)
    #                     raise Conflict()

    #                 logger.info("- Successfully found verified users: %s" % phone_number)
    #                 return result[0]

    #             elif user_id:
    #                 logger.debug("Finding userinfo with user_id: %s" % user_id)

    #                 result = []

    #                 userinfos = (
    #                     self.UsersInfos.select()
    #                     .where(
    #                         self.UsersInfos.userId == user_id
    #                     )
    #                 )

    #                 for userinfo in userinfos:
    #                     result.append(userinfo)

    #                 # check for no user
    #                 if len(result) < 1:
    #                     logger.error("Userinfo with user_id '%s' not found" % user_id)
    #                     raise Unauthorized()

    #                 # check for duplicate user
    #                 if len(result) > 1:
    #                     logger.error("Duplicate users found with user_id: %s" % user_id)
    #                     raise Conflict()

    #                 logger.info("- Successfully found user with user_id: %s" % user_id)
    #                 return result[0]

    #         elif table == "user":
    #             if phone_number:
    #                 try:
    #                     data = self.Data()
    #                     phone_number_hash = data.hash(data=phone_number)

    #                     user = self.UsersInfos.get(self.UsersInfos.full_phone_number == phone_number_hash, self.UsersInfos.status == "verified")
    #                 except self.UsersInfos.DoesNotExist:
    #                     logger.error("No user with phone_number '%s' found" % phone_number)
    #                     return None
    #                 else:
    #                     logger.info("- Successfully found user with phone_number '%s'" % phone_number)

    #                     return user

    #     except DatabaseError as err:
    #         logger.error("Failed finding user check logs")
    #         raise InternalServerError(err)
    
    def update(self, user_id: str, status: str = None) -> None:
        """
        """
        try:
            logger.debug("Finding userinfo with user_id: %s" % user_id)

            print(user_id)

            result = []

            userinfos = (
                self.UsersInfos.select()
                .where(
                    self.UsersInfos.userId == user_id
                )
                .dicts()
            )

            for userinfo in userinfos:
                result.append(userinfo)

            # check for no user
            if len(result) < 1:
                logger.error("Userinfo with user_id '%s' not found" % user_id)
                raise Unauthorized()

            # check for duplicate user
            if len(result) > 1:
                logger.error("Duplicate users found with user_id: %s" % user_id)
                raise Conflict()

            logger.info("- Successfully found user with user_id: %s" % user_id)

            if status:
                logger.debug("updating userinfo status with user_id: '%s' ..." % user_id)

                upd_userinfo = (
                    self.UsersInfos.update(
                        status = status
                    )
                    .where(
                        self.UsersInfos.userId == result[0]["userId"],
                        self.UsersInfos.id == result[0]["id"]
                    )
                )

                upd_userinfo.execute()

                logger.info("- User status '%s' successfully updated" % user_id)

        except DatabaseError as err:
            logger.error("updating user '%s' failed check logs" % user_id)
            raise InternalServerError(err)

    def recaptcha(self, captchaToken: str, remoteIp: str) -> bool:
        """
        """
        try:
            logger.debug("Starting recaptcha verification ...")
            if ENABLE_RECAPTCHA:
                url = f"https://www.google.com/recaptcha/api/siteverify?secret={SECRET_KEY}&response={captchaToken}&remoteip={remoteIp}"

                res = requests.post(url=url)

                json_res = res.json()

                if json_res["success"]:
                    logger.info("- Successfully verified recaptcha")
                    return True
                else:
                    logger.error("Invalid recaptcha token")
                    raise BadRequest()

            else:
                logger.info("- Recaptcha is turn off")
                return True

        except BadRequest:
            raise BadRequest()

        except Exception as error:
            logger.error("Failed verifying recaptcha check logs")
            raise InternalServerError(error)