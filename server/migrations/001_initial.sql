-- Initial PostgreSQL schema, aligned with docs/backend/DB_MODELS.md.
-- The migration runner owns the transaction and records the checksum.
-- Referenced history is restricted; only parent-to-item deletion cascades.

CREATE TYPE discount_type AS ENUM ('NONE', 'FIXED', 'PERCENTAGE');
CREATE TYPE quote_status AS ENUM ('DRAFT', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CONVERTED');
CREATE TYPE invoice_status AS ENUM ('DRAFT', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED');

CREATE FUNCTION set_updated_at() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(30),
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE business_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
    business_name VARCHAR(160) NOT NULL,
    logo_url TEXT,
    email VARCHAR(255),
    phone VARCHAR(30),
    address TEXT,
    tax_number VARCHAR(100),
    default_currency CHAR(3) NOT NULL DEFAULT 'KES',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name VARCHAR(160) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX clients_user_id_idx ON clients(user_id);
CREATE INDEX clients_user_name_idx ON clients(user_id, name);

CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    quote_number VARCHAR(40) NOT NULL,
    issue_date DATE NOT NULL,
    expiry_date DATE,
    currency CHAR(3) NOT NULL,
    subtotal NUMERIC(14,2) NOT NULL CHECK (subtotal >= 0),
    tax_rate NUMERIC(6,3) NOT NULL DEFAULT 0 CHECK (tax_rate >= 0),
    tax_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    discount_type discount_type NOT NULL DEFAULT 'NONE',
    discount_value NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (discount_value >= 0),
    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    total NUMERIC(14,2) NOT NULL CHECK (total >= 0),
    status quote_status NOT NULL DEFAULT 'DRAFT',
    notes TEXT,
    terms TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, quote_number),
    CHECK (expiry_date IS NULL OR expiry_date >= issue_date)
);
CREATE INDEX quotes_user_id_idx ON quotes(user_id);
CREATE INDEX quotes_client_id_idx ON quotes(client_id);
CREATE INDEX quotes_created_at_idx ON quotes(created_at);
CREATE INDEX quotes_user_status_idx ON quotes(user_id, status);

CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity NUMERIC(12,3) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(14,2) NOT NULL CHECK (line_total >= 0),
    position INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX quote_items_quote_id_idx ON quote_items(quote_id);

CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    source_quote_id UUID UNIQUE REFERENCES quotes(id) ON DELETE RESTRICT,
    invoice_number VARCHAR(40) NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE,
    currency CHAR(3) NOT NULL,
    subtotal NUMERIC(14,2) NOT NULL CHECK (subtotal >= 0),
    tax_rate NUMERIC(6,3) NOT NULL DEFAULT 0 CHECK (tax_rate >= 0),
    tax_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    discount_type discount_type NOT NULL DEFAULT 'NONE',
    discount_value NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (discount_value >= 0),
    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    total NUMERIC(14,2) NOT NULL CHECK (total >= 0),
    status invoice_status NOT NULL DEFAULT 'DRAFT',
    notes TEXT,
    terms TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, invoice_number),
    CHECK (due_date IS NULL OR due_date >= issue_date)
);
CREATE INDEX invoices_user_id_idx ON invoices(user_id);
CREATE INDEX invoices_client_id_idx ON invoices(client_id);
CREATE INDEX invoices_created_at_idx ON invoices(created_at);
CREATE INDEX invoices_user_status_idx ON invoices(user_id, status);
-- source_quote_id UNIQUE already provides its lookup index.

CREATE TABLE invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity NUMERIC(12,3) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(14,2) NOT NULL CHECK (line_total >= 0),
    position INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX invoice_items_invoice_id_idx ON invoice_items(invoice_id);

CREATE TABLE receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    source_invoice_id UUID REFERENCES invoices(id) ON DELETE RESTRICT,
    receipt_number VARCHAR(40) NOT NULL,
    issue_date DATE NOT NULL,
    currency CHAR(3) NOT NULL,
    subtotal NUMERIC(14,2) NOT NULL CHECK (subtotal >= 0),
    tax_rate NUMERIC(6,3) NOT NULL DEFAULT 0 CHECK (tax_rate >= 0),
    tax_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    discount_type discount_type NOT NULL DEFAULT 'NONE',
    discount_value NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (discount_value >= 0),
    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    total NUMERIC(14,2) NOT NULL CHECK (total >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, receipt_number)
);
CREATE INDEX receipts_user_id_idx ON receipts(user_id);
CREATE INDEX receipts_client_id_idx ON receipts(client_id);
CREATE INDEX receipts_created_at_idx ON receipts(created_at);
CREATE INDEX receipts_source_invoice_id_idx ON receipts(source_invoice_id);

CREATE TABLE receipt_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_id UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity NUMERIC(12,3) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(14,2) NOT NULL CHECK (line_total >= 0),
    position INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX receipt_items_receipt_id_idx ON receipt_items(receipt_id);

CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER business_profiles_updated_at BEFORE UPDATE ON business_profiles
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER clients_updated_at BEFORE UPDATE ON clients
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER quotes_updated_at BEFORE UPDATE ON quotes
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER invoices_updated_at BEFORE UPDATE ON invoices
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER receipts_updated_at BEFORE UPDATE ON receipts
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
