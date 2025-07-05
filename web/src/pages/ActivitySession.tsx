import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import {
  ActivityItemSchema,
  ActivityAnswerCreateSchema,
  AnswerResponseSchema,
  FreeTextAnswerHintSchema,
  FreeTextQuestionConfigSchema,
  FullActivityDetailsSchema,
} from "../schemas/backend";
import { $fetch } from "../lib/api";
import { Button } from "../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"; // New import

// Force re-evaluation
function ActivitySession() {
  const { activityId } = useParams<{ activityId: string }>(); // Removed activityItemId
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [answerText, setAnswerText] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [hints, setHints] = useState<z.infer<typeof FreeTextAnswerHintSchema>[]>([]);
  const [currentActivityItem, setCurrentActivityItem] = useState<z.infer<typeof ActivityItemSchema> | null>(null); // New state for current item

  // Mutation to start an activity and get the first item
  const startActivityMutation = useMutation({
    mutationFn: async () => {
      if (!activityId) throw new Error("Activity ID is missing.");
      const response = await $fetch(`/activities/${activityId}/start`, { method: "POST" });
      return ActivityItemSchema.parse(response);
    },
    onSuccess: (data) => {
      setCurrentActivityItem(data);
      queryClient.invalidateQueries({ queryKey: ["activityDetails", activityId] }); // Invalidate to update activity status
    },
    onError: (err) => {
      console.error("Failed to start activity:", err);
      setFeedback(`Error starting activity: ${err?.message || "Unknown error"}`);
    },
  });

  // Fetch activity details and all its items
  const {
    data: fullActivityDetails, // Renamed to reflect FullActivityDetails
    isLoading: isLoadingActivity,
    isError: isErrorActivity,
    error: activityError,
  } = useQuery<z.infer<typeof FullActivityDetailsSchema>, Error, z.infer<typeof FullActivityDetailsSchema>, (string | undefined)[]>({
    queryKey: ["activityDetails", activityId],
    queryFn: async () => {
      if (!activityId) throw new Error("Activity ID is missing.");
      const response = await $fetch(`/activities/${activityId}/details`, { method: "GET" });
      return FullActivityDetailsSchema.parse(response); // Use FullActivityDetailsSchema
    },
    enabled: !!activityId,
  });

  // Use a useEffect to trigger startActivityMutation when activity data is available and idle
  React.useEffect(() => {
    if (fullActivityDetails?.activity && fullActivityDetails.activity.status === "IDLE") {
      startActivityMutation.mutate();
    }
  }, [fullActivityDetails, startActivityMutation]);

  // Mutation to submit an answer
  const submitAnswerMutation = useMutation({
    mutationFn: async ({ isCorrect, skip }: { isCorrect: boolean; skip: boolean }) => {
      if (!activityId || !currentActivityItem?.id) throw new Error("Activity or Activity Item ID is missing.");

      const answerPayload = {
        activity_item_id: currentActivityItem.id,
        skip: skip,
        is_correct: isCorrect,
        answer: {
          activity_type: "FREE_TEXT",
          text: answerText,
        },
      };
      const response = await $fetch(`/activities/${activityId}/items/${currentActivityItem.id}/answer`, {
        method: "POST",
        body: ActivityAnswerCreateSchema.parse(answerPayload),
      });
      return AnswerResponseSchema.parse(response);
    },
    onSuccess: (data) => {
      setFeedback(data.success_verdict ? "Correct!" : "Incorrect. Try again or skip.");
      setHints(data.hints);
      setAnswerText(""); // Clear input after submission

      queryClient.invalidateQueries({ queryKey: ["activityDetails", activityId] });
      queryClient.invalidateQueries({ queryKey: ["activities"] }); // Invalidate dashboard list

      if (data.activity_complete) {
        alert("Activity completed!");
        navigate("/dashboard"); // Go back to dashboard
      } else if (data.next_item_id) {
        // If there's a next item, we need to fetch its details to set it as currentActivityItem
        // The backend's /start endpoint returns the next item directly, so we can use that.
        // If the activity is already ongoing, we might need a separate endpoint to get the next item.
        // For now, we'll rely on the /start endpoint's behavior or a re-fetch of activity details
        // which might trigger a new /start if the activity is still IDLE.
        // Given the current backend, the simplest way to get the next item is to re-call /start
        // or navigate to the activity page again, which will trigger the initial /start logic.
        // However, the /start endpoint is for starting an IDLE activity.
        // The submit answer response gives us next_item_id. We need to fetch that specific item.
        // Let's assume for now that the `activityDetails` query will eventually update `currentActivityItem`
        // if the activity is ongoing and a new item is available.
        // For a more robust solution, a dedicated endpoint to get a specific activity item by ID would be ideal.
        // For now, we will just invalidate the activity details query, which will re-fetch the activity
        // and if the activity is still ONGOING, it will not call startActivityMutation again.
        // The `currentActivityItem` should be updated by the `startActivityMutation` or by a direct fetch.
        // Since `submitAnswerMutation` returns `next_item_id`, we should fetch that item.
        // Let's add a new query for `currentActivityItem` that depends on `next_item_id`.

        // For now, let's just invalidate and let the system re-evaluate.
        // A more direct approach would be to fetch the next item directly here.
        // For simplicity, I will just invalidate and rely on the `startActivityMutation`
        // or a new query for `currentActivityItem` if it's not set.
        alert("Moving to next item!");
        // Invalidate activity details to potentially trigger a new current item fetch if needed
        queryClient.invalidateQueries({ queryKey: ["activityDetails", activityId] });
        // We need to explicitly fetch the next item and set it.
        // This is a gap in the current API design if we can't get a specific item by ID without starting.
        // However, the OpenAPI spec has `/api/v1/activities/{activity_id}/items/{activity_item_id}`
        // So we can use that to fetch the next item.
        queryClient.fetchQuery({
          queryKey: ["activityItem", activityId, data.next_item_id],
          queryFn: async () => {
            if (!activityId || !data.next_item_id) throw new Error("Activity or Activity Item ID is missing.");
            const response = await $fetch(`/activities/${activityId}/items/${data.next_item_id}`, { method: "GET" });
            return ActivityItemSchema.parse(response);
          },
        }).then(nextItem => {
          setCurrentActivityItem(nextItem);
        }).catch(err => {
          console.error("Failed to fetch next activity item:", err);
          setFeedback(`Error fetching next item: ${err?.message || "Unknown error"}`);
        });
      } else {
        // If no next_item_id and not complete, it means current item needs more attempts or is terminal
        queryClient.invalidateQueries({ queryKey: ["activityDetails", activityId] });
      }
    },
    onError: (err) => {
      console.error("Failed to submit answer:", err);
      setFeedback(`Error: ${err?.message || "Unknown error"}`);
      setHints([]);
    },
  });

  const handleAnswerSubmit = (isCorrect: boolean) => {
    submitAnswerMutation.mutate({ isCorrect, skip: false });
  };

  const handleSkip = () => {
    submitAnswerMutation.mutate({ isCorrect: false, skip: true });
  };

  if (isLoadingActivity || startActivityMutation.isPending) {
    return <div className="p-4">Loading activity session...</div>;
  }

  if (isErrorActivity) {
    return (
      <div className="p-4 text-red-500">
        <h2 className="text-3xl font-bold mb-4">Error Loading Activity</h2>
        <p>Activity Error: {activityError?.message || "N/A"}</p>
        <Button onClick={() => navigate("/dashboard")}>Back to Dashboard</Button>
      </div>
    );
  }

  if (!fullActivityDetails) {
    return <div className="p-4">Activity not found.</div>;
  }

  const activity = fullActivityDetails.activity; // Extract activity from fullActivityDetails
  const activityItems = fullActivityDetails.activity_items; // Extract activity_items
  const activityAnswers = fullActivityDetails.activity_answers; // Extract activity_answers

  const isTerminal = currentActivityItem?.status === "SUCCESS" || currentActivityItem?.status === "RETRIES_EXHAUST" || currentActivityItem?.status === "SKIP";

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Activity: {activity.generated_title || `ID: ${activity.id.substring(0, 8)}`}</h1>

      <Tabs defaultValue="details" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="items">Activity Items</TabsTrigger>
        </TabsList>
        <TabsContent value="details" className="p-4 border rounded-md mt-4">
          <h2 className="text-xl font-semibold mb-2">Activity Details</h2>
          <p><strong>Status:</strong> {activity.status}</p>
          <p><strong>Created At:</strong> {new Date(activity.created_at).toLocaleString()}</p>

          <h3 className="text-lg font-semibold mt-4 mb-2">Activity Items Overview:</h3>
          {activityItems && activityItems.length > 0 ? (
            <ul className="list-disc list-inside ml-4">
              {activityItems.map((item, index) => (
                <li key={item.id}>
                  Item {index + 1}: Type - {item.activity_type}, Status - {item.status}, Prompt: {(item.question_config as z.infer<typeof FreeTextQuestionConfigSchema>).prompt}
                </li>
              ))}
            </ul>
          ) : (
            <p>No activity items found for this activity.</p>
          )}

          <h3 className="text-lg font-semibold mt-4 mb-2">Activity Answers Overview:</h3>
          {activityAnswers && activityAnswers.length > 0 ? (
            <ul className="list-disc list-inside ml-4">
              {activityAnswers.map((answer, index) => (
                <li key={answer.id}>
                  Answer {index + 1}: Item ID - {answer.activity_item_id.substring(0, 8)}, Correct - {answer.is_correct ? "Yes" : "No"}, Attempted At - {new Date(answer.attempted_at).toLocaleString()}
                </li>
              ))}
            </ul>
          ) : (
            <p>No answers found for this activity.</p>
          )}
        </TabsContent>
        <TabsContent value="items" className="p-4 border rounded-md mt-4">
          <h2 className="text-xl font-semibold mb-4">Activity Items</h2>
          {currentActivityItem ? (
            <>
              <h3 className="text-lg font-medium mb-2">Current Question: {(currentActivityItem.question_config as z.infer<typeof FreeTextQuestionConfigSchema>).prompt}</h3>

              {feedback && <div className={`mb-4 p-2 rounded ${feedback.startsWith("Correct") ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>{feedback}</div>}

              {hints.length > 0 && (
                <div className="mb-4 p-2 bg-yellow-100 text-yellow-700 rounded">
                  <h3 className="font-medium">Hints:</h3>
                  <ul className="list-disc list-inside">
                    {hints.map((hint, index) => (
                      <li key={index}>{hint.activity_type === "FREE_TEXT" ? "Consider your wording." : "Hint available."}</li>
                    ))}
                  </ul>
                </div>
              )}

              {!isTerminal ? (
                <form onSubmit={(e) => { e.preventDefault(); handleAnswerSubmit(false); }} className="space-y-4">
                  <div>
                    <label htmlFor="answer" className="block text-sm font-medium text-gray-700">
                      Your Answer
                    </label>
                    <input
                      type="text"
                      id="answer"
                      name="answer"
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                      required
                      disabled={submitAnswerMutation.isPending}
                    />
                  </div>
                  <div className="flex space-x-4">
                    <Button type="submit" disabled={submitAnswerMutation.isPending}>
                      {submitAnswerMutation.isPending ? "Submitting..." : "Submit Answer"}
                    </Button>
                    <Button
                      type="button"
                      onClick={handleSkip}
                      disabled={submitAnswerMutation.isPending}
                      variant="outline"
                    >
                      Skip
                    </Button>
                  </div>
                </form>
              ) : (
                <div className="mt-4 p-4 bg-gray-100 rounded">
                  <p className="text-lg font-medium">This activity item is {currentActivityItem.status.toLowerCase()}.</p>
                  <Button onClick={() => navigate("/dashboard")} className="mt-4">
                    Back to Dashboard
                  </Button>
                </div>
              )}
            </>
          ) : (
            <p>No activity item available. Start the activity to get the first item.</p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default ActivitySession;
