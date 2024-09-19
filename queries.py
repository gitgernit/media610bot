CREATE_INVITES_TABLE = """
        CREATE TABLE IF NOT EXISTS Invites (
            message_id INT PRIMARY KEY,
            user_id INT
        );
    """

INSERT_INVITE = """
        INSERT INTO Invites (message_id, user_id)
        VALUES (?, ?);
    """

DELETE_INVITE = """
        DELETE FROM Invites
        WHERE message_id = ?;
    """

GET_INVITE_USER_ID = """
        SELECT user_id FROM Invites
        WHERE message_id = ?;
    """
