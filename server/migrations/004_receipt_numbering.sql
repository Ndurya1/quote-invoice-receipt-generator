-- Internal allocation state; counters survive deletion of individual receipts.
CREATE TABLE receipt_number_counters (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE RESTRICT,
    last_number BIGINT NOT NULL CHECK (last_number > 0)
);

INSERT INTO receipt_number_counters (user_id, last_number)
SELECT user_id, MAX(substring(receipt_number FROM 5)::numeric)::bigint
FROM receipts
WHERE receipt_number ~ '^RCT-[0-9]+$'
GROUP BY user_id
HAVING MAX(substring(receipt_number FROM 5)::numeric) > 0;

CREATE FUNCTION protect_receipt_number() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.receipt_number IS DISTINCT FROM OLD.receipt_number THEN
        RAISE EXCEPTION 'Receipt number is immutable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER receipts_number_immutable BEFORE UPDATE ON receipts
FOR EACH ROW EXECUTE FUNCTION protect_receipt_number();


