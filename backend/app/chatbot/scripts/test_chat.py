from app.chatbot.service import chat


def main():

    print("=" * 50)
    print("CMU Student Support Agent (Developer Test)")
    print("=" * 50)

    while True:

        prompt = input("\nYou: ")

        if prompt.lower() in ["exit", "quit"]:
            print("\nGoodbye!")
            break

        response = chat(prompt)

        print(f"\nAssistant: {response}")


if __name__ == "__main__":
    main()