-- Internal allocation state; counters survive deletion of individual quotes.
CREATE TABLE quote_number_counters (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE RESTRICT,
    last_number BIGINT NOT NULL CHECK (last_number > 0)
);

INSERT INTO quote_number_counters (user_id, last_number)
SELECT user_id, MAX(substring(quote_number FROM 4)::numeric)::bigint
FROM quotes
WHERE quote_number ~ '^QT-[0-9]+$'
GROUP BY user_id
HAVING MAX(substring(quote_number FROM 4)::numeric) > 0;

CREATE FUNCTION protect_quote_number() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.quote_number IS DISTINCT FROM OLD.quote_number THEN
        RAISE EXCEPTION 'Quote number is immutable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER quotes_number_immutable BEFORE UPDATE ON quotes
FOR EACH ROW EXECUTE FUNCTION protect_quote_number();
