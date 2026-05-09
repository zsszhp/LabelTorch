"""Database initial migration - create core tables"""

from labeltorch.app.infra.db.sqlite import Database


def migrate(db: Database):
    """Run v001 initial migration: create 7 core tables"""

    # Projects table
    db.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            root_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Datasets table
    db.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            image_dir TEXT NOT NULL,
            label_dir TEXT NOT NULL,
            format TEXT NOT NULL DEFAULT 'yolo_txt',
            sample_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    # Dataset samples table
    db.execute("""
        CREATE TABLE IF NOT EXISTS dataset_samples (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
            image_path TEXT NOT NULL,
            label_path TEXT,
            width INTEGER,
            height INTEGER,
            status TEXT DEFAULT 'valid'
        )
    """)

    # Class mappings table
    db.execute("""
        CREATE TABLE IF NOT EXISTS class_mappings (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
            original_id INTEGER NOT NULL,
            mapped_id INTEGER NOT NULL,
            class_name TEXT NOT NULL
        )
    """)

    # Train jobs table
    db.execute("""
        CREATE TABLE IF NOT EXISTS train_jobs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            dataset_id TEXT NOT NULL REFERENCES datasets(id),
            model_family TEXT NOT NULL,
            config_json TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            metrics_json TEXT,
            log_path TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT
        )
    """)

    # Model versions table
    db.execute("""
        CREATE TABLE IF NOT EXISTS model_versions (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            job_id TEXT NOT NULL REFERENCES train_jobs(id),
            parent_version_id TEXT REFERENCES model_versions(id),
            best_pt_path TEXT,
            metrics_json TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Annotation changes table
    db.execute("""
        CREATE TABLE IF NOT EXISTS annotation_changes (
            id TEXT PRIMARY KEY,
            sample_id TEXT NOT NULL REFERENCES dataset_samples(id) ON DELETE CASCADE,
            action TEXT NOT NULL,
            boxes_json TEXT NOT NULL,
            source TEXT DEFAULT 'manual',
            created_at TEXT NOT NULL
        )
    """)

    # Export tasks table
    db.execute("""
        CREATE TABLE IF NOT EXISTS export_tasks (
            id TEXT PRIMARY KEY,
            version_id TEXT NOT NULL REFERENCES model_versions(id),
            format TEXT NOT NULL,
            options_json TEXT,
            status TEXT DEFAULT 'pending',
            output_path TEXT,
            created_at TEXT NOT NULL,
            finished_at TEXT
        )
    """)

    # Create indexes
    db.execute("CREATE INDEX IF NOT EXISTS idx_datasets_project ON datasets(project_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_samples_dataset ON dataset_samples(dataset_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_class_mapping_dataset ON class_mappings(dataset_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_train_jobs_project ON train_jobs(project_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_model_versions_project ON model_versions(project_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_annotation_changes_sample ON annotation_changes(sample_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_export_tasks_version ON export_tasks(version_id)")
