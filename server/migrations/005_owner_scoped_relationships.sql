-- Enforce tenant ownership at the database boundary for document relationships.
-- Service-layer ownership checks remain required for tenant-safe responses.

ALTER TABLE clients
    ADD CONSTRAINT clients_user_id_id_key UNIQUE (user_id, id);

ALTER TABLE quotes
    ADD CONSTRAINT quotes_user_id_id_key UNIQUE (user_id, id);

ALTER TABLE invoices
    ADD CONSTRAINT invoices_user_id_id_key UNIQUE (user_id, id);

ALTER TABLE quotes
    DROP CONSTRAINT quotes_client_id_fkey,
    ADD CONSTRAINT quotes_client_id_fkey
        FOREIGN KEY (user_id, client_id) REFERENCES clients (user_id, id) ON DELETE RESTRICT;

ALTER TABLE invoices
    DROP CONSTRAINT invoices_client_id_fkey,
    DROP CONSTRAINT invoices_source_quote_id_fkey,
    ADD CONSTRAINT invoices_client_id_fkey
        FOREIGN KEY (user_id, client_id) REFERENCES clients (user_id, id) ON DELETE RESTRICT,
    ADD CONSTRAINT invoices_source_quote_id_fkey
        FOREIGN KEY (user_id, source_quote_id) REFERENCES quotes (user_id, id) ON DELETE RESTRICT;

ALTER TABLE receipts
    DROP CONSTRAINT receipts_client_id_fkey,
    DROP CONSTRAINT receipts_source_invoice_id_fkey,
    ADD CONSTRAINT receipts_client_id_fkey
        FOREIGN KEY (user_id, client_id) REFERENCES clients (user_id, id) ON DELETE RESTRICT,
    ADD CONSTRAINT receipts_source_invoice_id_fkey
        FOREIGN KEY (user_id, source_invoice_id) REFERENCES invoices (user_id, id) ON DELETE RESTRICT;
