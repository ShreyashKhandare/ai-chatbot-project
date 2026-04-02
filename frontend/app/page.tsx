import dynamic from "next/dynamic"

const ClientOnly = dynamic(() => import("./ClientPage"), {
  ssr: false,
})

export default function Page() {
  return <ClientOnly />
}