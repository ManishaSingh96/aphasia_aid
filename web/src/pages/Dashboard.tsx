import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { ActivitySchema, ActivityItemSchema } from "../schemas/backend";
import { $fetch } from "../lib/api";
import { Button } from "../components/ui/button";

function Dashboard() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Query to list all activities
  const {
    data: activities,
    isLoading: isLoadingActivities,
    isError: isErrorActivities,
    error: activitiesError,
  } = useQuery({
    queryKey: ["activities"],
    queryFn: async () => {
      const response = await $fetch("/activities/", { method: "GET" });
      return ActivitySchema.array().parse(response);
    },
  });

  // Mutation to create a new activity
  const createActivityMutation = useMutation({
    mutationFn: async () => {
      // No input needed for now, as per backend spec.
      // TODO: Add parameters for activity generation when backend supports it.
      const response = await $fetch("@post/activities/create");
      return ActivitySchema.parse(response);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      alert("New activity created successfully!");
    },
    onError: (err) => {
      console.error("Failed to create activity:", err);
      alert("Failed to create activity. Please try again.");
    },
  });

  // Mutation to start an activity
  const startActivityMutation = useMutation({
    mutationFn: async (activityId: string) => {
      const response = await $fetch(`/activities/${activityId}/start`, { method: "POST" });
      return ActivityItemSchema.parse(response); // Explicitly parse and type the response
    },
    onSuccess: (data: z.infer<typeof ActivityItemSchema>, activityId) => {
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      alert(`Activity ${activityId} started!`);
      // Navigate to the individual activity page
      navigate(`/activity/${activityId}`);
    },
    onError: (err) => {
      console.error("Failed to start activity:", err);
      alert("Failed to start activity. Please try again.");
    },
  });

  if (isLoadingActivities) {
    return (
      <div className="p-4">
        <h2 className="text-3xl font-bold mb-4">Dashboard Page</h2>
        <p className="text-lg">Loading activities...</p>
      </div>
    );
  }

  if (isErrorActivities) {
    return (
      <div className="p-4 text-red-500">
        <h2 className="text-3xl font-bold mb-4">Dashboard Page</h2>
        <p className="text-lg">
          Error loading activities: {activitiesError?.message || "Unknown error"}
        </p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-3xl font-bold mb-4">Dashboard</h2>
      <div className="flex space-x-4 mb-6">
        <Button onClick={() => createActivityMutation.mutate()} disabled={createActivityMutation.isPending}>
          {createActivityMutation.isPending ? "Creating..." : "Create New Activity"}
        </Button>
        <Button onClick={() => navigate("/profile-settings")}>
          Go to Profile Settings
        </Button>
      </div>

      <h3 className="text-2xl font-semibold mb-4">Your Activities:</h3>
      {activities && activities.length > 0 ? (
        <ul className="space-y-4">
          {activities.map((activity) => (
            <li key={activity.id} className="border p-4 rounded-lg shadow-sm">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-xl font-medium">
                    {activity.generated_title || `Activity ${activity.id.substring(0, 8)}`}
                  </p>
                  <p className="text-gray-600 text-sm">Status: {activity.status}</p>
                  <p className="text-gray-600 text-sm">Created: {new Date(activity.created_at).toLocaleString()}</p>
                </div>
                {activity.status === "IDLE" && (
                  <Button
                    onClick={() => startActivityMutation.mutate(activity.id)}
                    disabled={startActivityMutation.isPending}
                  >
                    {startActivityMutation.isPending ? "Starting..." : "Start Activity"}
                  </Button>
                )}
                {activity.status === "ONGOING" && (
                  <Button onClick={() => navigate(`/activity/${activity.id}`)}>
                    Continue Activity
                  </Button>
                )}
                {activity.status === "COMPLETED" && (
                  <Button onClick={() => navigate(`/activity/${activity.id}`)}>
                    View Details
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-lg">No activities found. Create a new one to get started!</p>
      )}
    </div>
  );
}

export default Dashboard;
