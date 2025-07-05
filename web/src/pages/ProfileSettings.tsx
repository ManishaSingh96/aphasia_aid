import React, { useEffect, useState } from "react";
import { ProfileSchema } from "../schemas/backend"; // PatientMetadataSchema is no longer directly used
import { $fetch } from "../lib/api";
import { Button } from "../components/ui/button";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../components/ui/form";
import { Input } from "../components/ui/input";

type Profile = z.infer<typeof ProfileSchema>;

// Define a Zod schema for the form validation
const formSchema = z.object({
  patient_name: z.string().min(1, "Patient Name is required"),
  patient_age: z.coerce.number().min(0, "Age must be a non-negative number"),
  city: z.string(),
  language: z.string(),
  diagnosis: z.string(),
  patient_address: z.string().nullable(), // This one was nullable in backend schema
  state: z.string().nullable(), // This one was nullable in backend schema
  country: z.string().nullable(), // This one was nullable in backend schema
  profession: z.string().nullable(), // This one was nullable in backend schema
  education: z.string().nullable(), // This one was nullable in backend schema
});

type ProfileFormValues = z.infer<typeof formSchema>;

const ProfileSettings: React.FC = () => {
  const [apiError, setApiError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(true); // Keep loading for initial fetch

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      patient_name: "",
      patient_age: 0,
      city: "",
      language: "",
      diagnosis: "",
      patient_address: null,
      state: null,
      country: null,
      profession: null,
      education: null,
    },
  });

  // Effect to fetch initial profile data and set form values
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const fetchedProfile: Profile = await $fetch("@get/profile/");
        const initialFormValues: ProfileFormValues = {
          patient_name: fetchedProfile.metadata.patient_name,
          patient_age: fetchedProfile.metadata.patient_age,
          city: fetchedProfile.metadata.city,
          language: fetchedProfile.metadata.language,
          diagnosis: fetchedProfile.metadata.diagnosis,
          patient_address: fetchedProfile.metadata.patient_address,
          state: fetchedProfile.metadata.state,
          country: fetchedProfile.metadata.country,
          profession: fetchedProfile.metadata.profession,
          education: fetchedProfile.metadata.education,
        };
        form.reset(initialFormValues, undefined);
      } catch (err) {
        console.error("Failed to fetch profile:", err);
        setApiError("Failed to load profile data.");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [form]);

  const onSubmit = async (values: ProfileFormValues) => {
    setLoading(true);
    setApiError(null);
    setSuccess(false);

    try {
      // The API expects PatientMetadata directly for the PUT request
      // Ensure all fields are sent, even if optional, as per backend schema
      const updatedProfile: Profile = await $fetch("@post/profile/", {
        method: "PUT",
        body: values, // values from react-hook-form
      });
      console.log("Profile updated successfully:", updatedProfile);
      setSuccess(true);
      // Optionally, re-fetch profile or update form with response data if needed
      // Map the updatedProfile (which is of type Profile) to ProfileFormValues
      const resetValues: ProfileFormValues = {
        patient_name: updatedProfile.metadata.patient_name,
        patient_age: updatedProfile.metadata.patient_age,
        city: updatedProfile.metadata.city,
        language: updatedProfile.metadata.language,
        diagnosis: updatedProfile.metadata.diagnosis,
        patient_address: updatedProfile.metadata.patient_address,
        state: updatedProfile.metadata.state,
        country: updatedProfile.metadata.country,
        profession: updatedProfile.metadata.profession,
        education: updatedProfile.metadata.education,
      };
      form.reset(resetValues); // Update form with actual response from backend
    } catch (err: unknown) {
      console.error("Failed to update profile:", err);
      if (err instanceof Error) {
        setApiError(err.message);
      } else {
        setApiError("Failed to update profile. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Profile Settings</h1>
      {loading ? (
        <div className="text-blue-500 mb-4">Loading profile data...</div>
      ) : (
        <>
          {success && (
            <div className="text-green-500 mb-4">Profile updated successfully!</div>
          )}
          {apiError && <div className="text-red-500 mb-4">Error: {apiError}</div>}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="patient_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Patient Name</FormLabel>
                    <FormControl>
                      <Input placeholder="John Doe" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="patient_age"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Patient Age</FormLabel>
                    <FormControl>
                      <Input type="number" placeholder="30" {...field} value={String(field.value ?? 0)} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="city"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>City</FormLabel>
                    <FormControl>
                      <Input placeholder="New York" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Language</FormLabel>
                    <FormControl>
                      <Input placeholder="English" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="diagnosis"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Diagnosis</FormLabel>
                    <FormControl>
                      <Input placeholder="Aphasia" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="patient_address"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Patient Address</FormLabel>
                    <FormControl>
                      <Input placeholder="123 Main St" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="state"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>State</FormLabel>
                    <FormControl>
                      <Input placeholder="NY" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="country"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Country</FormLabel>
                    <FormControl>
                      <Input placeholder="USA" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="profession"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Profession</FormLabel>
                    <FormControl>
                      <Input placeholder="Engineer" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="education"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Education</FormLabel>
                    <FormControl>
                      <Input placeholder="Masters" {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" disabled={form.formState.isSubmitting || loading}>
                {loading ? "Loading Profile..." : (form.formState.isSubmitting ? "Saving..." : "Save Profile")}
              </Button>
            </form>
          </Form>
        </>
      )}
    </div>
  );
};

export default ProfileSettings;
