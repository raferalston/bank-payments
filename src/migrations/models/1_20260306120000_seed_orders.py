from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    DO $$
    BEGIN
        IF (SELECT COUNT(*) FROM "order") = 0 THEN
            INSERT INTO "order" (amount, payment_status) VALUES
                (1000.00, 'not_paid'),
                (2500.50, 'not_paid'),
                (750.00, 'partially_paid'),
                (5000.00, 'partially_paid'),
                (320.00, 'paid'),
                (15000.00, 'paid');
        END IF;
    END $$;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return ""


# Состояние моделей без изменений (только данные)
MODELS_STATE = (
    "eJztmV9z2jgQwL8K46d0hsskNGk7eXPAXHwlQInT3rXpeBZbgCay5NhyU6bDd68k2/gvNE"
    "1T6vZ4g9WutPtbIe2KL5rHXETCw1HgokA7a33RKHhIfCgOtFsa+H4mlgIOU6I02VplGvIA"
    "HC6EMyAhEiIXhU6AfY4ZFVIaESKFzBGKmM4zUUTxXYRszuaIL5QnHz4KMaYu+ozC9Kt/a8"
    "8wIm7BUezKtZXc5ktfyUzK+0pRrja1HUYij2bK/pIvGF1rY8qldI4oCoAjOT0PIum+9C4J"
    "M40o9jRTiV3M2bhoBhHhuXAfyMBhVPIT3oQqwLlc5a/O8cnLk1fPX5y8EirKk7Xk5SoOL4"
    "s9NlQEhpa2UuPAIdZQGDNu4LEoDrzIrocc7AGp55cZlRi6sdVhYl3mmdLbBjQVZESzXfQ0"
    "SLfw6hld81IfHBx32p1n0vvwjmCuQnurT7oX+uTg5OiZQpoh9GHpIcrtkAOPwirK7gICg0"
    "aeYmkKV4A6qMK0OkuJrQjhZ/HUKOO2D/HPokhVG44se6ybPUEzUbqhY31imfpg8F8y4kPA"
    "MRCyXI/H0mTCb29yDz7bBNE5X8idfbQlQ2kaOkcqP0ycNPH5M0xGOmqomCEnQJKYDXUbXY"
    "xw7KH6nV60LO/2xPQw/dDM/a6JGNwRJcvkdNpC1zIvjStLvxzLSLxQ7H6FSLcMOdJR0mVJ"
    "evCilIn1JK13pnXRkl9b70dDQxFkIZ8HasVMz3qvSZ8g4sym7N4GN3eQptIUTCGxke8+Mr"
    "FFy31if2lilfPyap/d5i4pKZiCc3sPgWsXRipnb82pe55Y9l9PEAGFtpropLwZx7M0M8ur"
    "dOum0jww1mGbiFWHvI5XlgCFufJari1XKhGpqQVzsDZXg35OaV8P7uvB/2M9qCD8YDWYzr"
    "G7WrCWpdbVry7OWg6Eixuqd99cmxNz+PdZC5y7CCu4jajzmC9xCJd/sBavm2eH1biPqJsy"
    "LaZhbAx7CnyickN7xnh0ZVqGqLddJC5hsTtFAT4x+tfDnhQGaBaJtYSsr5sDKZkBJqghhf"
    "kU6K2d7vW6I1vmq/7MqTF9VIqS83mXZVsR6unpQ6ienm7GKsfKRxB+TFGcM3uCinj3ZH+T"
    "AjgNe2trs+9Z/4jWZt+z/qGJTZzPFR/yAbz2EtvYd+RNvt19NCSBT9CAVFr9EsUqwj4LEJ"
    "7T12hZqdzqW/r1PxbNI7ipoRfiAO7XvWxhd4gARVgobj1EMd7Ve4a22vxC8jPfBnQUYGeh"
    "1TwNJCPtbS8DkOnsHwYa9rtsb3kY+ISCMHlEe2iJnjP5xf1rk2pz+dP4DoiJ+u8J8PjoIS"
    "2j0NoIUI2V/s1hlKO6N6p/rkbDDSVxZlICeU1FgB9c7PB2i+CQf2wm1i0UZdSFCimFd3Cp"
    "/1vm2h2Mzsulj5zgvO5W3uX1svoKc4Vyeg=="
)
