export async function verifyFace(voterId: string, imageFile: File): Promise<boolean> {
    try {
        const formData = new FormData();
        formData.append("voter_id", voterId);
        formData.append("challenge_type", "smile"); // as requested, default challenge type
        formData.append("file", imageFile);

        const response = await fetch("http://localhost:8000/verify", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            console.error(`Verification failed with status: ${response.status}`);
            return false;
        }

        const data = await response.json();
        return !!data.verified;
    } catch (error) {
        console.error("Error during face verification:", error);
        return false;
    }
}