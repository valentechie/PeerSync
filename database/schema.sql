BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE users (
    id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    email VARCHAR(320) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_users PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

-- Running upgrade 0001 -> 0002

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

-- Running upgrade 0002 -> 0003

CREATE TABLE skills (
    id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    CONSTRAINT pk_skills PRIMARY KEY (id)
);

CREATE UNIQUE INDEX uq_skills_name_lower ON skills (lower(name));

CREATE TABLE match_requests (
    id UUID NOT NULL, 
    requester_id UUID NOT NULL, 
    receiver_id UUID NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    score INTEGER NOT NULL, 
    score_breakdown JSONB NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    responded_at TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT pk_match_requests PRIMARY KEY (id), 
    CONSTRAINT ck_match_requests_not_self CHECK (requester_id <> receiver_id), 
    CONSTRAINT ck_match_requests_score_range CHECK (score BETWEEN 0 AND 100), 
    CONSTRAINT fk_match_requests_receiver_id_users FOREIGN KEY(receiver_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_match_requests_requester_id_users FOREIGN KEY(requester_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT ck_match_requests_match_status CHECK (status IN ('pending', 'accepted', 'rejected', 'cancelled'))
);

CREATE INDEX ix_match_requests_receiver_id ON match_requests (receiver_id);

CREATE INDEX ix_match_requests_requester_id ON match_requests (requester_id);

CREATE UNIQUE INDEX uq_match_requests_pending_pair ON match_requests (requester_id, receiver_id) WHERE status = 'pending';

CREATE TABLE profiles (
    user_id UUID NOT NULL, 
    bio TEXT NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_profiles PRIMARY KEY (user_id), 
    CONSTRAINT fk_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE user_skills (
    user_id UUID NOT NULL, 
    skill_id UUID NOT NULL, 
    kind VARCHAR(20) NOT NULL, 
    CONSTRAINT pk_user_skills PRIMARY KEY (user_id, skill_id, kind), 
    CONSTRAINT fk_user_skills_skill_id_skills FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE, 
    CONSTRAINT fk_user_skills_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT ck_user_skills_skill_kind CHECK (kind IN ('offering', 'seeking'))
);

CREATE INDEX ix_user_skills_skill_id ON user_skills (skill_id);

CREATE TABLE study_sessions (
    id UUID NOT NULL, 
    match_id UUID NOT NULL, 
    objective VARCHAR(300) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    scheduled_at TIMESTAMP WITH TIME ZONE, 
    started_at TIMESTAMP WITH TIME ZONE, 
    ended_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_study_sessions PRIMARY KEY (id), 
    CONSTRAINT fk_study_sessions_match_id_match_requests FOREIGN KEY(match_id) REFERENCES match_requests (id) ON DELETE CASCADE, 
    CONSTRAINT ck_study_sessions_session_status CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled'))
);

CREATE INDEX ix_study_sessions_match_id ON study_sessions (match_id);

CREATE TABLE contrasta_rounds (
    id UUID NOT NULL, 
    session_id UUID NOT NULL, 
    prompt TEXT NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    revealed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_contrasta_rounds PRIMARY KEY (id), 
    CONSTRAINT fk_contrasta_rounds_session_id_study_sessions FOREIGN KEY(session_id) REFERENCES study_sessions (id) ON DELETE CASCADE, 
    CONSTRAINT ck_contrasta_rounds_contrasta_status CHECK (status IN ('individual', 'revealed'))
);

CREATE INDEX ix_contrasta_rounds_session_id ON contrasta_rounds (session_id);

CREATE TABLE messages (
    id UUID NOT NULL, 
    session_id UUID NOT NULL, 
    sender_id UUID NOT NULL, 
    content TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_messages PRIMARY KEY (id), 
    CONSTRAINT fk_messages_sender_id_users FOREIGN KEY(sender_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_messages_session_id_study_sessions FOREIGN KEY(session_id) REFERENCES study_sessions (id) ON DELETE CASCADE
);

CREATE INDEX ix_messages_session_id ON messages (session_id);

CREATE TABLE session_reviews (
    id UUID NOT NULL, 
    session_id UUID NOT NULL, 
    reviewer_id UUID NOT NULL, 
    reviewee_id UUID NOT NULL, 
    rating INTEGER NOT NULL, 
    comment TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_session_reviews PRIMARY KEY (id), 
    CONSTRAINT ck_session_reviews_rating_range CHECK (rating BETWEEN 1 AND 5), 
    CONSTRAINT ck_session_reviews_not_self CHECK (reviewer_id <> reviewee_id), 
    CONSTRAINT fk_session_reviews_reviewee_id_users FOREIGN KEY(reviewee_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_session_reviews_reviewer_id_users FOREIGN KEY(reviewer_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_session_reviews_session_id_study_sessions FOREIGN KEY(session_id) REFERENCES study_sessions (id) ON DELETE CASCADE, 
    CONSTRAINT uq_session_reviews_one_per_reviewer UNIQUE (session_id, reviewer_id)
);

CREATE INDEX ix_session_reviews_reviewee_id ON session_reviews (reviewee_id);

CREATE TABLE studymind_hints (
    id UUID NOT NULL, 
    session_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    question TEXT NOT NULL, 
    level INTEGER NOT NULL, 
    hint TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_studymind_hints PRIMARY KEY (id), 
    CONSTRAINT ck_studymind_hints_level_range CHECK (level BETWEEN 1 AND 3), 
    CONSTRAINT fk_studymind_hints_session_id_study_sessions FOREIGN KEY(session_id) REFERENCES study_sessions (id) ON DELETE CASCADE, 
    CONSTRAINT fk_studymind_hints_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_studymind_hints_session_id ON studymind_hints (session_id);

CREATE TABLE teachback_submissions (
    id UUID NOT NULL, 
    session_id UUID NOT NULL, 
    explainer_id UUID NOT NULL, 
    concept VARCHAR(200) NOT NULL, 
    explanation TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_teachback_submissions PRIMARY KEY (id), 
    CONSTRAINT fk_teachback_submissions_explainer_id_users FOREIGN KEY(explainer_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_teachback_submissions_session_id_study_sessions FOREIGN KEY(session_id) REFERENCES study_sessions (id) ON DELETE CASCADE
);

CREATE INDEX ix_teachback_submissions_session_id ON teachback_submissions (session_id);

CREATE TABLE contrasta_answers (
    id UUID NOT NULL, 
    round_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    answer TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_contrasta_answers PRIMARY KEY (id), 
    CONSTRAINT fk_contrasta_answers_round_id_contrasta_rounds FOREIGN KEY(round_id) REFERENCES contrasta_rounds (id) ON DELETE CASCADE, 
    CONSTRAINT fk_contrasta_answers_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_contrasta_answers_one_per_user UNIQUE (round_id, user_id)
);

CREATE TABLE teachback_peer_reviews (
    id UUID NOT NULL, 
    submission_id UUID NOT NULL, 
    reviewer_id UUID NOT NULL, 
    comment TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_teachback_peer_reviews PRIMARY KEY (id), 
    CONSTRAINT fk_teachback_peer_reviews_reviewer_id_users FOREIGN KEY(reviewer_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_teachback_peer_reviews_submission_id_teachback_submissions FOREIGN KEY(submission_id) REFERENCES teachback_submissions (id) ON DELETE CASCADE, 
    CONSTRAINT uq_teachback_peer_reviews_submission_id UNIQUE (submission_id)
);

CREATE TABLE teachback_ai_feedback (
    id UUID NOT NULL, 
    peer_review_id UUID NOT NULL, 
    correctness TEXT NOT NULL, 
    clarity TEXT NOT NULL, 
    completeness TEXT NOT NULL, 
    examples TEXT NOT NULL, 
    uncertainty TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_teachback_ai_feedback PRIMARY KEY (id), 
    CONSTRAINT fk_teachback_ai_feedback_peer_review_id_teachback_peer_reviews FOREIGN KEY(peer_review_id) REFERENCES teachback_peer_reviews (id) ON DELETE CASCADE, 
    CONSTRAINT uq_teachback_ai_feedback_peer_review_id UNIQUE (peer_review_id)
);

ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY;

ALTER TABLE contrasta_answers ENABLE ROW LEVEL SECURITY;

ALTER TABLE contrasta_rounds ENABLE ROW LEVEL SECURITY;

ALTER TABLE match_requests ENABLE ROW LEVEL SECURITY;

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

ALTER TABLE session_reviews ENABLE ROW LEVEL SECURITY;

ALTER TABLE skills ENABLE ROW LEVEL SECURITY;

ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

ALTER TABLE studymind_hints ENABLE ROW LEVEL SECURITY;

ALTER TABLE teachback_ai_feedback ENABLE ROW LEVEL SECURITY;

ALTER TABLE teachback_peer_reviews ENABLE ROW LEVEL SECURITY;

ALTER TABLE teachback_submissions ENABLE ROW LEVEL SECURITY;

ALTER TABLE user_skills ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

-- Running upgrade 0003 -> 0004

ALTER TABLE users ADD COLUMN google_sub VARCHAR(255);

CREATE UNIQUE INDEX ix_users_google_sub ON users (google_sub);

ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

UPDATE alembic_version SET version_num='0004' WHERE alembic_version.version_num = '0003';

-- Running upgrade 0004 -> 0005

ALTER TABLE users ADD COLUMN supabase_user_id UUID;

CREATE UNIQUE INDEX ix_users_supabase_user_id ON users (supabase_user_id);

DROP INDEX ix_users_google_sub;

ALTER TABLE users DROP COLUMN google_sub;

UPDATE alembic_version SET version_num='0005' WHERE alembic_version.version_num = '0004';

-- Running upgrade 0005 -> 0006

ALTER TABLE study_sessions ALTER COLUMN match_id DROP NOT NULL;

ALTER TABLE study_sessions ADD COLUMN title VARCHAR(120) DEFAULT '' NOT NULL;

ALTER TABLE study_sessions ALTER COLUMN title DROP DEFAULT;

ALTER TABLE study_sessions ADD COLUMN created_by_id UUID;

ALTER TABLE study_sessions ADD CONSTRAINT fk_study_sessions_created_by_id_users FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE CASCADE;

CREATE TABLE session_participants (
    session_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_session_participants PRIMARY KEY (session_id, user_id), 
    CONSTRAINT fk_session_participants_session_id_study_sessions FOREIGN KEY(session_id) REFERENCES study_sessions (id) ON DELETE CASCADE, 
    CONSTRAINT fk_session_participants_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_session_participants_user_id ON session_participants (user_id);

ALTER TABLE session_participants ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='0006' WHERE alembic_version.version_num = '0005';

-- Running upgrade 0006 -> 0007

CREATE TABLE friendships (
    user_a_id UUID NOT NULL, 
    user_b_id UUID NOT NULL, 
    requester_id UUID NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_friendships PRIMARY KEY (user_a_id, user_b_id), 
    CONSTRAINT ck_friendships_friendship_status CHECK (status IN ('pending', 'accepted')), 
    CONSTRAINT ck_friendships_not_self CHECK (user_a_id <> user_b_id), 
    CONSTRAINT fk_friendships_user_a_id_users FOREIGN KEY(user_a_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_friendships_user_b_id_users FOREIGN KEY(user_b_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_friendships_requester_id_users FOREIGN KEY(requester_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_friendships_user_b_id ON friendships (user_b_id);

ALTER TABLE friendships ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='0007' WHERE alembic_version.version_num = '0006';

-- Running upgrade 0007 -> 0008

ALTER TABLE profiles ADD COLUMN study_code VARCHAR(60);

CREATE INDEX ix_profiles_study_code ON profiles (study_code);

UPDATE alembic_version SET version_num='0008' WHERE alembic_version.version_num = '0007';

-- Running upgrade 0008 -> 0009

CREATE TABLE message_attachments (
    id UUID NOT NULL, 
    message_id UUID NOT NULL, 
    file_name VARCHAR(200) NOT NULL, 
    content_type VARCHAR(50) NOT NULL, 
    size INTEGER NOT NULL, 
    data BYTEA NOT NULL, 
    CONSTRAINT pk_message_attachments PRIMARY KEY (id), 
    CONSTRAINT fk_message_attachments_message_id_messages FOREIGN KEY(message_id) REFERENCES messages (id) ON DELETE CASCADE, 
    CONSTRAINT uq_message_attachments_message_id UNIQUE (message_id)
);

ALTER TABLE message_attachments ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='0009' WHERE alembic_version.version_num = '0008';

-- Running upgrade 0009 -> 0010

ALTER TABLE session_reviews DROP CONSTRAINT uq_session_reviews_one_per_reviewer;

ALTER TABLE session_reviews ADD CONSTRAINT uq_session_reviews_one_per_pair UNIQUE (session_id, reviewer_id, reviewee_id);

ALTER TABLE session_reviews ADD COLUMN clarity INTEGER NOT NULL;

ALTER TABLE session_reviews ADD CONSTRAINT ck_session_reviews_clarity_range CHECK (clarity BETWEEN 1 AND 5);

ALTER TABLE session_reviews ADD COLUMN listening INTEGER NOT NULL;

ALTER TABLE session_reviews ADD CONSTRAINT ck_session_reviews_listening_range CHECK (listening BETWEEN 1 AND 5);

ALTER TABLE session_reviews ADD COLUMN preparation INTEGER NOT NULL;

ALTER TABLE session_reviews ADD CONSTRAINT ck_session_reviews_preparation_range CHECK (preparation BETWEEN 1 AND 5);

UPDATE alembic_version SET version_num='0010' WHERE alembic_version.version_num = '0009';

COMMIT;

