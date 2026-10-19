import LakeProfile from "@/components/lake-profile";
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <LakeProfile id={id} />;
}
