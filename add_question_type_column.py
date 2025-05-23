#!/usr/bin/env python
import asyncio
from sqlalchemy import text
from app.dao.session_maker import get_async_session


async def add_question_type_column():
    """Add the question_type column to interviews table if it doesn't exist."""
    print("Starting script to add question_type column...")
    try:
        async for session in get_async_session():
            try:
                # Check if the column already exists
                check_query = text(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='interviews' AND column_name='question_type';
                """
                )

                print("Checking if column exists...")
                result = await session.execute(check_query)
                column_exists = result.scalar() is not None

                print(f"Column exists: {column_exists}")

                if not column_exists:
                    # Add the column if it doesn't exist
                    print("Adding question_type column to interviews table...")
                    add_column_query = text(
                        """
                        ALTER TABLE interviews 
                        ADD COLUMN question_type VARCHAR DEFAULT 'pythonn' NOT NULL;
                    """
                    )
                    await session.execute(add_column_query)
                    await session.commit()
                    print("Column added successfully!")
                else:
                    print(
                        "Column 'question_type' already exists in the interviews table."
                    )

                break  # We only need one session
            except Exception as e:
                print(f"Error in session: {str(e)}")
                raise
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    print("Script started")
    asyncio.run(add_question_type_column())
    print("Script finished")
