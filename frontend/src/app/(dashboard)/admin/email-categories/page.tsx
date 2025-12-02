import EmailCategoryManager from "@/components/emails/category-manager";

export const metadata = {
  title: "Email Categories – Admin",
  description: "Review and correct AI email categories to improve training data",
};

export default function EmailCategoriesPage() {
  return <EmailCategoryManager />;
}
