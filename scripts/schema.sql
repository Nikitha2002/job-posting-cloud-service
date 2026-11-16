CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_records INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES processing_jobs(id),
    status TEXT NOT NULL DEFAULT 'pending',
    record_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS job_postings (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES processing_jobs(id),
    batch_id UUID REFERENCES batches(id),
    source_row INTEGER NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    description TEXT,
    UNIQUE(job_id, source_row)
);

CREATE TABLE IF NOT EXISTS job_skills (
    posting_id BIGINT NOT NULL REFERENCES job_postings(id)
        ON DELETE CASCADE,
    skill TEXT NOT NULL,
    PRIMARY KEY(posting_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_job_postings_title
    ON job_postings(title);

CREATE INDEX IF NOT EXISTS idx_job_postings_location
    ON job_postings(location);

CREATE INDEX IF NOT EXISTS idx_job_skills_skill
    ON job_skills(skill);
