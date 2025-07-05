-- +goose Up
-- +goose StatementBegin
CREATE TABLE profile (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    metadata JSONB NOT NULL
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE profile;
-- +goose StatementEnd
