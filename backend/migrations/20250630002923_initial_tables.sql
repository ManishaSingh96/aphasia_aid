-- +goose Up
-- +goose StatementBegin
CREATE TYPE activity_status AS ENUM ('IDLE', 'ONGOING', 'COMPLETED');
CREATE TYPE activity_item_status AS ENUM (
  'NOT_TERMINATED',
  'RETRIES_EXHAUST', -- terminal state
  'SKIP', -- ternminal state
  'SUCCESS' -- terminal state
);
CREATE TYPE activity_item_type AS ENUM ('FREE_TEXT'); -- we can add more types later

CREATE TABLE activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status activity_status NOT NULL DEFAULT 'IDLE',
    generated_title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE activity_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES activity(id) ON DELETE CASCADE,
    activity_type activity_item_type NOT NULL,
    -- JSONB schema is handled application side based on activity_type
    question_config JSONB NOT NULL, -- what we ask
    question_evaluation_config JSONB NOT NULL, -- how we evaluate answer
    max_retries INT NOT NULL DEFAULT 2,
    attempted_retries INT NOT NULL DEFAULT 0,
    status activity_item_status NOT NULL DEFAULT 'NOT_TERMINATED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE activity_answer (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_item_id UUID NOT NULL REFERENCES activity_item(id) ON DELETE CASCADE,
    -- answer schema will be specific to activity_item.activity_type
    answer JSONB NOT NULL,
    is_correct BOOLEAN NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE activity_answer;
DROP TABLE activity_item;
DROP TABLE activity;
DROP TYPE activity_item_type;
DROP TYPE activity_status;
-- +goose StatementEnd
