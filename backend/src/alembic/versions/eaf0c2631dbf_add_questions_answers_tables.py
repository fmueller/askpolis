"""add_questions_answers_tables

Revision ID: eaf0c2631dbf
Revises: e25be9ff9c7e
Create Date: 2025-05-13 21:21:15.286359

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eaf0c2631dbf"
down_revision: str | None = "e25be9ff9c7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "question_document",
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id", "document_id"),
    )
    op.create_table(
        "question_parliament",
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("parliament_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["parliament_id"], ["parliaments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id", "parliament_id"),
    )
    op.create_table(
        "question_party",
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("party_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id", "party_id"),
    )
    op.create_table(
        "answers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("parliament_id", sa.UUID(), nullable=True),
        sa.Column("parliament_period_id", sa.UUID(), nullable=True),
        sa.Column("party_id", sa.UUID(), nullable=True),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(parliament_id IS NOT NULL OR parliament_period_id IS NOT NULL "
            "OR party_id IS NOT NULL OR document_id IS NOT NULL)",
            name="ck_answers_at_least_one_dimension",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parliament_id"], ["parliaments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parliament_period_id"], ["parliament_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "question_id", "parliament_id", "parliament_period_id", "party_id", "document_id", name="uq_answers_dims"
        ),
    )
    op.create_table(
        "question_parliament_period",
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("parliament_period_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["parliament_period_id"], ["parliament_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id", "parliament_period_id"),
    )
    op.create_table(
        "answer_contents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer_id", sa.UUID(), nullable=False),
        sa.Column("language", sa.CHAR(length=5), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("translated_from", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("answer_id", "language", name="uq_answer_contents_answer_id_lang"),
    )


def downgrade() -> None:
    op.drop_table("answer_contents")
    op.drop_table("question_parliament_period")
    op.drop_table("answers")
    op.drop_table("question_party")
    op.drop_table("question_parliament")
    op.drop_table("question_document")
    op.drop_table("questions")
