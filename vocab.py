import os
import sys
import time
import msvcrt
import pickle
import datetime
import numpy as np
import pandas as pd


def clearScreen():
    '''Clear output console screen'''
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')


def readInputWithTimeout(prompt, timeout=15):
    start_time = time.time()
    print(prompt, end=' ')
    sys.stdout.flush()
    has_timed_out = False
    while True:
        if msvcrt.kbhit():
            _ = msvcrt.getche()
            break
        if (time.time() - start_time) > timeout:
            has_timed_out = True
            print('(Oops! Time up)')
            break

    return has_timed_out


def saveRevisionResult(
        attempted_word_count,
        correct_words,
        incorrect_words
    ):
    '''Save the performace report'''
    df = pd.DataFrame({
        'correct': pd.Series(correct_words, dtype='object'),
        'incorrect': pd.Series(incorrect_words, dtype='object')
    })

    dt = datetime.datetime.now()
    filename = f'{dt.strftime("%Y%m%d_%H%M")}_{attempted_word_count}'

    df.to_csv(f'performance/{filename}.csv')


def getIncorrectlyAnsweredWords(dir_name='performance'):
    performance_files = [
        os.path.join(dir_name, f) for f in os.listdir(dir_name)
        if os.path.isfile(os.path.join(dir_name, f))
    ]

    incorrect_word_list = []
    for f in performance_files:
        word_df = pd.read_csv(f, dtype=str, encoding='latin-1')
        incorrect_word_list += list(word_df['incorrect'])
        incorrect_word_list = list(set(incorrect_word_list))

    if incorrect_word_list.index(np.nan) >= 0:
        incorrect_word_list.remove(np.nan)

    return incorrect_word_list


def selectDatabaseSubset(
        filepath='data/WordDatabase.csv',
        choice=1,
        N=-1,
        character=None
    ):
    word_df = pd.read_csv(filepath, dtype=str, encoding='latin-1')

    if choice == 0:
        word_df = None
    elif choice == 2:
        last_record = word_df.iloc[-1, 0:2]
        word_df = word_df[
            (word_df['date'] == last_record['date']) &
            (word_df['session'] == last_record['session'])
        ]
    elif choice == 3:
        unique_dates = word_df['date'].unique()
        if (N > len(unique_dates)):
            print('The given value of N is too large')
            sys.exit(0)
        elif (N <= 0):
            print('The value of N must be positive')
            sys.exit(0)

        n_dates = unique_dates[-1 * N:]
        word_df = word_df[
            word_df['date'].isin(n_dates)
        ]
    elif choice == 4:
        word_df = word_df[
            word_df['word'].str.get(0).isin([
                character.lower(),
                character.upper()
            ])
        ]
    elif choice == 5:
        incorrect_word_list = getIncorrectlyAnsweredWords(
            dir_name='performance'
        )
        word_df = word_df[
            word_df['word'].isin(incorrect_word_list)
        ]

    return word_df


def startRevision(
        word_df,
        retrieved_checkpoint=False,
        checkpoint_filepath=None
    ):
    '''Use word database to revise the contents'''

    if not retrieved_checkpoint:
        df = word_df.copy()
        correct_words = []
        incorrect_words = []
        attempted_word_count = 0
    else:
        data = pickle.load(open(checkpoint_filepath, 'rb'))
        word_df = data['word_df']
        df = data['df']
        correct_words = data['correct_words']
        incorrect_words = data['incorrect_words']
        attempted_word_count = data['attempted_word_count']

    while(df.shape[0] > 0):
        word_row = df.sample()
        word_index = word_row.index
        word_row = word_row.to_dict(orient='records')
        word_row = word_row[0]

        print(f'\033[1;31;40m')
        print(
            f"WORD {attempted_word_count + 1}/{word_df.shape[0]}: {word_row['word']}")

        print(f'\033[0;37;40m')
        has_timed_out = readInputWithTimeout('Show Solution?')

        print(f'\033[0;33;40m')
        print(f"MEANING: {word_row['meaning']}\n")
        print(f"SYNONYMS: {word_row['synonym_1']}; {word_row['synonym_2']}\n")
        print(f"SENTENCE 1: {word_row['sentence_1']}")
        print(f"SENTENCE 2: {word_row['sentence_2']}")

        df = df.drop(word_index, axis=0)

        if not has_timed_out:
            print(f'\033[0;32;40m')
            result = input('Did you get it right? (Enter \'N\' to deny)\n')
        else:
            result = 'n'
        if result in ['N', 'n']:
            incorrect_words.append(word_row['word'])
        else:
            correct_words.append(word_row['word'])

        attempted_word_count += 1

        print(f'\033[0;37;40m')
        show_next = input('Show Next? (Enter \'N\' to deny)\n')
        if show_next in ['N', 'n']:
            save_confirm = input(
                '\nDo you wish to save? (Enter \'N\' to deny)\n')
            if save_confirm in ['N', 'n']:
                break
            data = {
                'word_df': word_df,
                'df': df,
                'correct_words': correct_words,
                'incorrect_words': incorrect_words,
                'attempted_word_count': attempted_word_count
            }
            existing_checkpoint = input(
                '\nUse existing checkpoint? (Enter \'N\' to deny)\n')
            if existing_checkpoint in ['N', 'n']:
                checkpoint_name = input('\nEnter checkoint name: \n')
            else:
                for index, filename in enumerate(os.listdir('checkpoint')):
                    print(f'{index}: {filename}')
                checkpoint_file_index = int(input('\nEnter your choice: '))
                checkpoint_name = os.listdir('checkpoint')[
                    checkpoint_file_index]
                checkpoint_name = checkpoint_name[:checkpoint_name.rindex('.')]
            pickle.dump(data, open(f'checkpoint/{checkpoint_name}.pkl', 'wb'))
            clearScreen()
            print(
                f'Checkpoint saved. You revised {attempted_word_count} words.')
            return
        clearScreen()

    print(f'\033[0;32;40m')
    print(f'Revision completed. You revised {attempted_word_count} words.')
    print(f'Performance: {len(correct_words)}/{attempted_word_count}')
    if len(incorrect_words) > 0:
        print('\n\nIncorrect Words:')
        for index, incorrect_word in enumerate(incorrect_words):
            print(f'{index + 1}: {incorrect_word}')
    saveRevisionResult(
        attempted_word_count,
        correct_words,
        incorrect_words
    )

    if retrieved_checkpoint:
        os.remove(checkpoint_filepath)


def main():
    '''Driver Function'''
    print(f'\033[0;37;40m')
    clearScreen()

    if len(os.listdir('checkpoint')) > 0:
        print('0: Resume checkpoint')
    print('1: Revise entire database')
    print('2: Revise last session')
    print('3: Revise last N days')
    print('4: Challenge yourself')
    print('5: Learn from mistakes')
    choice = int(input('\nEnter your choice: '))

    clearScreen()
    if choice == 0:
        for index, filename in enumerate(os.listdir('checkpoint')):
            print(f'{index}: {filename}')
        file_index = int(input('\nEnter your choice: '))
        checkpoint_filepath = f"checkpoint/{os.listdir('checkpoint')[file_index]}"

    if choice == 3:
        N = int(input('\nEnter the value of N: '))
    else:
        N = -1

    if choice == 4:
        character = input('\nEnter a character: ')
    else:
        character = None

    clearScreen()
    word_df = selectDatabaseSubset(
        filepath='data/WordDatabase.csv',
        choice=choice,
        N=N,
        character=character
    )

    retrieved_checkpoint = True if choice == 0 else False
    checkpoint_filepath = None if not choice == 0 else checkpoint_filepath

    startRevision(word_df, retrieved_checkpoint, checkpoint_filepath)


if __name__ == '__main__':
    main()
