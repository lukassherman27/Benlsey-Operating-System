import EmailCategoryManager from "@/components/emails/category-manager";

export const metadata = {
  title: "Email Intelligence – Category Corrections",
  description: "Review and correct AI email categories to improve training data",
};

export default function EmailsPage() {
  return <EmailCategoryManager />;
}
