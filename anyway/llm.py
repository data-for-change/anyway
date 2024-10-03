from openai import OpenAI
import json
import tiktoken

from langchain.output_parsers import PydanticOutputParser, EnumOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import langchain
from enum import Enum
from anyway import secrets

api_key = secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

langchain.debug = True
model = ChatOpenAI(api_key=api_key, temperature=0)


def match_streets_with_langchain(street_names, location):
    street_names.append("-")
    Streets = Enum('Streets', {name: name for name in street_names})

    parser = EnumOutputParser(enum=Streets)
    print(parser.get_format_instructions())
    prompt = PromptTemplate(
        template="Return the street that is mentioned in the location string. if non matches return '-'.\nstreets: {streets}\n" +
                 "location_string:{location}\n{format_instructions}\n",
        input_variables=["streets", "location"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser

    res = chain.invoke({"streets": street_names, "location": location})
    return res


def count_tokens_for_prompt(messages, model):
    tokenizer = tiktoken.encoding_for_model(model)
    total_tokens = 0
    for message in messages:
        # Each message has a role and content
        message_tokens = tokenizer.encode(f"{message['role']}: {message['content']}")
        total_tokens += len(message_tokens)
        # Additional tokens for formatting
        total_tokens += 4  # approx overhead for each message (role + delimiters)

    return total_tokens


def count_tokens(text, model):
    tokenizer = tiktoken.encoding_for_model(model)
    tokens = tokenizer.encode(text)
    return len(tokens)


def ask_gpt(system_message, user_message, model="gpt-4o"):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    completion = client.chat.completions.create(
        response_format={"type": "json_object"},
        model=model,
        messages=messages
    )
    print(f"tokens for prompt: {count_tokens_for_prompt(messages, model)}")
    return completion.choices[0].message


def ask_ai_about_street_matching(streets, location_string, model="gpt-4-turbo"):
    system_message = """
    Given a list of streets, return the name of the street that is mentioned in the provided location string.
    Return the name exactly as appears in list.
    If no match is found, return "-".
    Return json with field "street" and your answer.
    Select one of the following options: 
    """ + json.dumps(streets + ["-"])
    input = json.dumps({"streets": streets, "location": location_string})
    reply = ask_gpt(system_message, input, model)
    # print(f"tokens: {count_tokens(reply.content, model)}")
    result = json.loads(reply.content)["street"]
    return result, result in streets
