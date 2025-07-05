import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "../../lib/utils";
declare const Tabs: React.ForwardRefExoticComponent<Omit<React.ComponentPropsWithoutRef<typeof TabsPrimitive.Root>, "ref"> & React.RefAttributes<React.ElementRef<typeof TabsPrimitive.Root>>>;
declare const TabsList: React.ForwardRefExoticComponent<Omit<React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>, "ref"> & React.RefAttributes<React.ElementRef<typeof TabsPrimitive.List>>>;
declare const TabsTrigger: React.ForwardRefExoticComponent<Omit<React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>, "ref"> & React.RefAttributes<React.ElementRef<typeof TabsPrimitive.Trigger>>>;
declare const TabsContent: React.ForwardRefExoticComponent<Omit<React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>, "ref"> & React.RefAttributes<React.ElementRef<typeof TabsPrimitive.Content>>>;
export { Tabs, TabsList, TabsTrigger, TabsContent };
