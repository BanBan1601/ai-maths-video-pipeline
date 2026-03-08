# Video State Machine

```text
NEW
  -> IDEA_GENERATING
  -> IDEA_REVIEW
     -> IDEA_REJECTED -> IDEA_GENERATING
     -> IDEA_APPROVED
        -> RESEARCHING
        -> SCRIPT_GENERATING
        -> SCRIPT_REVIEW
           -> SCRIPT_REJECTED -> SCRIPT_GENERATING
           -> SCRIPT_APPROVED
              -> STORYBOARDING
              -> MANIM_GENERATING
              -> NARRATION_GENERATING
              -> COMPOSITION_PENDING
              -> QA_RUNNING
                 -> QA_FAILED_AUTO_REPAIR -> QA_RUNNING
                 -> QA_FAILED_MANUAL -> SCRIPT_GENERATING or MANIM_GENERATING
                 -> FINAL_REVIEW
                    -> FINAL_REJECTED -> SCRIPT_GENERATING or MANIM_GENERATING
                    -> FINAL_APPROVED
                       -> UPLOAD_READY
                       -> UPLOAD_REVIEW
                          -> UPLOAD_REJECTED -> UPLOAD_READY
                          -> UPLOAD_APPROVED
                             -> UPLOADING
                                -> PUBLISHED_YOUTUBE
                                -> PUBLISHED_INSTAGRAM
                                -> PUBLISHED_ALL
```

## Approval gates
- Idea review
- Script review
- Final video review
- Upload review

## Rejection handling
Every rejection stores:
- reviewer feedback
- failing stage
- requested correction type
- whether a new step should be proposed

If the system infers a missing quality-control step from feedback, it creates a `pipeline_change_proposal` item that requires separate approval before altering the workflow.
