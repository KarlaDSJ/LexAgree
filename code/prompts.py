prompts_messages = {
'identify_arguments': [
        {"role": "user", "content":  """You are a legal expert working at the European Court of Human Rights (ECHR).
            You will be provided with an extract of a court decision. Your task is to identify all arguments within the text.

            Task:
            An argument consists of a claim (the main point being made) and one or more premises (assumptions or evidence supporting the claim).
            Important: An argument cannot consist of only a claim. It must include at least one premise.

            Guidelines for Identifying Arguments:
            A claim is the main point or conclusion being made in the argument.
            A premise provides evidence or assumptions that support the claim. It may present information that is taken to be true for the purposes of the argument.
            The claim and premises must be presented exactly as they appear in the text without any modifications, paraphrasing, or alterations.

            Additional Instructions:
            Referencing Legal Texts and Precedents:
            Legal references, such as Articles from legal texts or references to prior cases, can be used as part of the argument. They may serve as claims or premises within the argument.
            Article references or precedent cases should be considered carefully, as they could support or challenge the main claim or premise.

            Argument Structures:
            Arguments can have the following structures, which you can follow to generate your output:
            - Deductive arguments: Where a premise supports a claim. This is the typical structure but not the only one.
            - Counter-arguments: Where a premise attacks or challenges the claim. These arguments should also be identified and extracted.
            - Argument from position to know: Example: "X asserts P. X knows if P is true or not. X would assert what they know about P."
            - Argument from established rule: Example: "For all x, if doing A is the established rule for x, then x must do A (subject to exceptional cases)."
            - Argument from precedent case: Example: "Case C0 would set a precedent with respect to an existing rule R. Case C0 is similar to case C1. C1 needs to be treated equally with respect to rule R as case C0."

            Preferred Structure:
            Prefer one large argument over splitting it into multiple smaller ones, if both options would convey the same meaning. Group relevant premises and claims together as part of the same argument for clarity and coherence.

            Formatting:
            For each argument:
            - First, provide the argument number.
            - Then, the claim followed by its premises, each listed with a dash beneath the claim.
            - Ensure that claims and premises are taken exactly as they appear in the text.
            
            Formatting:
            - For each argument, provide first the number of the argument, then 
            - The claim and list the corresponding premises beneath the claim, each marked with a dash.
            Formatting Example:
                1. Argument
                **Claim:** {put claim here}
                **Premises:**
                - {premise 1}
                - {premise 2}
                ...
        Here is the text: """},
    ],
}