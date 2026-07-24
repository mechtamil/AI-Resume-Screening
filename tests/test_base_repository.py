"""
============================================================
RecruitOS

Module      : Base Repository Test
Sprint      : 5.5.1
Version     : 1.0.0
Author       : Tamilvanan A

============================================================
"""

import pandas as pd

from services.base_repository import BaseRepository


def main():

    dataframe = pd.DataFrame(

        {

            "Skill": [

                "Python",

                "SQL",

                "Python",

                None

            ],

            "Category": [

                "Programming",

                "Database",

                "Programming",

                "Database"

            ],

            "Active": [

                "Yes",

                "No",

                "Yes",

                "Yes"

            ]

        }

    )

    print("\n" + "=" * 60)

    print("RecruitOS Base Repository Test")

    print("=" * 60)

    print("\nOriginal DataFrame")

    print(dataframe)

    print("\nNormalize Text")

    print(

        BaseRepository.normalize_text(

            "  Python  "

        )

    )

    print("\nClean List")

    sample = [

        "Python",

        "python",

        "",

        None,

        "SQL"

    ]

    print(

        BaseRepository.clean_list(sample)

    )

    print("\nRemove Duplicates")

    print(

        BaseRepository.remove_duplicates(

            [

                "A",

                "A",

                "B",

                "C",

                "C"

            ]

        )

    )

    print("\nColumn Values")

    print(

        BaseRepository.get_column(

            dataframe,

            "Skill"

        )

    )

    print("\nClean Column")

    print(

        BaseRepository.get_clean_column(

            dataframe,

            "Skill"

        )

    )

    print("\nExists")

    print(

        BaseRepository.exists(

            dataframe,

            "Skill",

            "Python"

        )

    )

    print("\nSearch")

    print(

        BaseRepository.search(

            dataframe,

            "Skill",

            "SQL"

        )

    )

    print("\nActive Records")

    print(

        BaseRepository.filter_active(

            dataframe

        )

    )

    print("\nDictionary")

    print(

        BaseRepository.dataframe_to_dict(

            dataframe,

            "Skill",

            "Category"

        )

    )

    print("\nStatistics")

    print(

        BaseRepository.total_records(

            dataframe

        )

    )

    print(

        BaseRepository.total_columns(

            dataframe

        )

    )

    print(

        BaseRepository.is_empty(

            dataframe

        )

    )

    BaseRepository.display_summary(

        dataframe,

        "Skill Repository"

    )


if __name__ == "__main__":

    main()