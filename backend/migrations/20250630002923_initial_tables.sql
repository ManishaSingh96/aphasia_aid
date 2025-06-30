-- +goose Up
-- +goose StatementBegin
CREATE TYPE activity_status AS ENUM ('IDLE', 'ONGOING', 'COMPLETED');
CREATE TYPE activity_item_type AS ENUM ('FREE_TEXT', 'MULTIPLE_CHOICE');

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
    prompt_config JSONB NOT NULL,
    evaluation_config JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE activity_answer (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_item_id UUID NOT NULL REFERENCES activity_item(id) ON DELETE CASCADE,
    response_data JSONB NOT NULL,
    accuracy_score NUMERIC(5, 2),
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
