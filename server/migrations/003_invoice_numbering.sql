-- Internal allocation state; counters survive deletion of individual invoices.
CREATE TABLE invoice_number_counters (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE RESTRICT,
    last_number BIGINT NOT NULL CHECK (last_number > 0)
);

INSERT INTO invoice_number_counters (user_id, last_number)
SELECT user_id, MAX(substring(invoice_number FROM 5)::numeric)::bigint
FROM invoices
WHERE invoice_number ~ '^INV-[0-9]+$'
GROUP BY user_id
HAVING MAX(substring(invoice_number FROM 5)::numeric) > 0;

CREATE FUNCTION protect_invoice_number() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.invoice_number IS DISTINCT FROM OLD.invoice_number THEN
        RAISE EXCEPTION 'Invoice number is immutable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER invoices_number_immutable BEFORE UPDATE ON invoices
FOR EACH ROW EXECUTE FUNCTION protect_invoice_number();

